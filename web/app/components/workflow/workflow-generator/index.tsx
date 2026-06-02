'use client'
import type { GeneratedGraph } from './types'
import type { FormValue } from '@/app/components/header/account-setting/model-provider-page/declarations'
import type { CompletionParams, Model, ModelModeType } from '@/types/app'
import {
  AlertDialog,
  AlertDialogActions,
  AlertDialogCancelButton,
  AlertDialogConfirmButton,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogTitle,
} from '@langgenius/dify-ui/alert-dialog'
import { Button } from '@langgenius/dify-ui/button'
import { Dialog, DialogContent } from '@langgenius/dify-ui/dialog'
import { Textarea } from '@langgenius/dify-ui/textarea'
import { toast } from '@langgenius/dify-ui/toast'
import { useBoolean } from 'ahooks'
import * as React from 'react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import IdeaOutput from '@/app/components/app/configuration/config/automatic/idea-output'
import VersionSelector from '@/app/components/app/configuration/config/automatic/version-selector'
import { Generator } from '@/app/components/base/icons/src/vender/other'
import { ModelTypeEnum } from '@/app/components/header/account-setting/model-provider-page/declarations'
import { useModelListAndDefaultModelAndCurrentProviderAndModel } from '@/app/components/header/account-setting/model-provider-page/hooks'
import ModelParameterModal from '@/app/components/header/account-setting/model-provider-page/model-parameter-modal'
import WorkflowPreview from '@/app/components/workflow/workflow-preview'
import { useAppContext } from '@/context/app-context'
import { useLocalStorage } from '@/hooks/use-local-storage'
import { useRouter } from '@/next/navigation'
import { generateWorkflow } from '@/service/debug'
import { getRedirectionPath } from '@/utils/app-redirection'
import { applyToCurrentApp, applyToNewApp, WorkflowApplyHashCollisionError, WorkflowApplyOrphanError } from './apply'
import ExamplePrompts from './example-prompts'
import GenerationPhases from './generation-phases'
import RefineNode from './refine-node'
import { useWorkflowGeneratorStore } from './store'
import useGenGraph from './use-gen-graph'

const STORAGE_MODEL_KEY = 'workflow-gen-model'
const FE_TIMEOUT_MS = 60_000

// Empty starting point handed to ``useLocalStorage`` as the SSR / first-open
// default — also used to gate the "Generate" button (``model.name === ''``
// means we haven't resolved a provider yet).
const EMPTY_MODEL: Model = {
  name: '',
  provider: '',
  mode: 'chat' as unknown as ModelModeType.chat,
  completion_params: {} as CompletionParams,
}

const renderPlaceholder = (label: string) => (
  <div className="flex h-full w-0 grow flex-col items-center justify-center space-y-3 px-8">
    <Generator className="size-8 text-text-quaternary" />
    <div className="text-center text-[13px] leading-5 font-normal text-text-tertiary">
      {label}
    </div>
  </div>
)

// AbortController throws a DOMException in modern browsers and a plain
// Error in older / non-DOM environments — accept both so we don't toast
// for an abort the user intentionally triggered.
const isAbortError = (e: unknown): boolean =>
  (e instanceof DOMException || e instanceof Error) && e.name === 'AbortError'

const WorkflowGeneratorModal: React.FC = () => {
  const { t } = useTranslation('workflow')
  const router = useRouter()
  const { isCurrentWorkspaceEditor } = useAppContext()

  const isOpen = useWorkflowGeneratorStore(s => s.isOpen)
  const mode = useWorkflowGeneratorStore(s => s.mode)
  const currentAppId = useWorkflowGeneratorStore(s => s.currentAppId)
  const currentAppMode = useWorkflowGeneratorStore(s => s.currentAppMode)
  const closeGenerator = useWorkflowGeneratorStore(s => s.closeGenerator)

  // Persisted via ``useLocalStorage`` so the user's last-picked model and
  // completion params survive a page reload — the live state IS the storage
  // value, no parallel ``useState`` / manual ``localStorage.setItem`` calls.
  // Mandatory per ``web/CLAUDE.md``: no direct ``localStorage`` access in
  // app code.
  const [model, setModel] = useLocalStorage<Model>(STORAGE_MODEL_KEY, EMPTY_MODEL)

  const { defaultModel } = useModelListAndDefaultModelAndCurrentProviderAndModel(ModelTypeEnum.textGeneration)

  // Hydrate from the workspace default once the catalogue loads. Effect-set
  // is required because ``defaultModel`` resolves async after the provider
  // catalogue fetch completes.
  useEffect(() => {
    if (defaultModel && !model.name) {
      setModel(prev => ({
        ...(prev ?? EMPTY_MODEL),
        name: defaultModel.model,
        provider: defaultModel.provider.provider,
      }))
    }
  }, [defaultModel, model.name, setModel])

  const handleModelChange = useCallback((newValue: { modelId: string, provider: string, mode?: string, features?: string[] }) => {
    setModel(prev => ({
      ...(prev ?? EMPTY_MODEL),
      provider: newValue.provider,
      name: newValue.modelId,
      mode: newValue.mode as ModelModeType,
    }))
  }, [setModel])

  const handleCompletionParamsChange = useCallback((newParams: FormValue) => {
    setModel(prev => ({
      ...(prev ?? EMPTY_MODEL),
      completion_params: newParams as CompletionParams,
    }))
  }, [setModel])

  const [instruction, setInstruction] = useState('')
  const [ideaOutput, setIdeaOutput] = useState('')

  const storageKey = `${mode}-${currentAppId ?? 'new'}`
  const { addVersion, current, currentVersionIndex, setCurrentVersionIndex, versions } = useGenGraph({
    storageKey,
  })

  const [isLoading, { setTrue: setLoadingTrue, setFalse: setLoadingFalse }] = useBoolean(false)
  const [isApplying, { setTrue: setApplyingTrue, setFalse: setApplyingFalse }] = useBoolean(false)

  // Per-attempt nonce — bumped on each Generate click so ``GenerationPhases``
  // can reset its internal phase timer instead of resuming wherever the
  // previous attempt left off (which makes the UI look wedged).
  const [startedAt, setStartedAt] = useState(0)

  // Confirmation dialog for "Apply to current draft" — the only remaining
  // AlertDialog now that the hash-collision case is surfaced via the toast's
  // ``actionProps`` (Reload button) instead of a second blocking modal.
  const [isShowConfirmOverwrite, { setTrue: showConfirmOverwrite, setFalse: hideConfirmOverwrite }] = useBoolean(false)

  // Holds the AbortController of the in-flight ``/workflow-generate`` request
  // so we can cancel it on (a) modal close, (b) a second Generate click
  // while loading, (c) the hard 60 s frontend timeout, or (d) the user
  // pressing Cancel. Without this an in-flight request outlives the modal
  // and can race a future Generate call.
  const abortRef = useRef<AbortController | null>(null)
  // Companion timer so the timeout doesn't keep running after the response
  // lands. Cleared inside the same ``finally`` block that flips loading off.
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  // Mode the user generated against. If they switch app context mid-flight
  // (e.g. open the same modal from a different Studio in another tab) we
  // hide the "Apply to current" button so the wrong-mode graph never lands
  // in the wrong Studio. Captured at Generate time, not Apply time.
  const generatedModeRef = useRef<typeof mode | null>(null)

  const clearTimers = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
  }, [])

  const abortInFlight = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort()
      abortRef.current = null
    }
    clearTimers()
  }, [clearTimers])

  // Cleanup on unmount — a modal unmount mid-generation must NOT leave the
  // request running in the background (it would still resolve, mutate the
  // store, and toast "applied" against a stale modal).
  useEffect(() => {
    return () => {
      abortInFlight()
    }
    // The cleanup function reads refs only, so it's stable; we intentionally
    // exclude ``abortInFlight`` from deps to avoid re-running this effect on
    // every render.
    // eslint-disable-next-line react/exhaustive-deps
  }, [])

  // Note: the modal is mounted lazily by ``mount.tsx`` which unmounts it when
  // ``isOpen`` flips to false, so transient state (instruction / ideaOutput)
  // resets implicitly on the next open. No reset effect needed.

  const isValid = () => {
    const trimmed = instruction.trim()
    if (!trimmed) {
      toast.error(t('workflowGenerator.instructionRequired'))
      return false
    }
    if (!model.name) {
      // No usable model resolved (provider catalogue empty or still
      // loading). Without this guard the request would fly with an empty
      // ``model_config.name`` and surface as a backend 400 — not actionable
      // for the user. Tell them to pick a model.
      toast.error(t('workflowGenerator.modelRequired'))
      return false
    }
    return true
  }

  const onGenerate = async () => {
    if (!isValid())
      return
    // Cancel any previous in-flight request (double-click guard). The
    // previous promise will reject with AbortError which our catch swallows.
    abortInFlight()

    setStartedAt(Date.now())
    generatedModeRef.current = mode
    setLoadingTrue()

    // Hard frontend timeout — aborts the request and surfaces a localised
    // toast so the user sees something actionable instead of a perpetual
    // spinner if the backend hangs.
    timeoutRef.current = setTimeout(() => {
      abortRef.current?.abort()
      abortRef.current = null
      toast.error(t('workflowGenerator.errors.timeout'))
    }, FE_TIMEOUT_MS)

    try {
      const res = await generateWorkflow({
        mode,
        instruction,
        ideal_output: ideaOutput,
        model_config: model,
      }, {
        getAbortController: (c) => { abortRef.current = c },
      })
      const first = res.errors?.[0]
      if (first) {
        // Prefer the localised copy for the structured code; fall back to
        // the backend's human-readable ``detail`` for codes we don't have
        // a translation for yet.
        const i18nKey = `workflowGenerator.errors.${first.code}`
        const localised = t(i18nKey, { defaultValue: '' })
        toast.error(localised || first.detail || res.error || t('workflowGenerator.generateFailed'))
        return
      }
      if (res.error) {
        toast.error(res.error)
        return
      }
      addVersion(res)
    }
    catch (e: unknown) {
      // Aborts are intentional (modal close, second click, timeout) — never
      // toast for them. The timeout path already showed its own toast.
      if (isAbortError(e))
        return
      const message = e instanceof Error ? e.message : ''
      toast.error(message || t('workflowGenerator.generateFailed'))
    }
    finally {
      setLoadingFalse()
      clearTimers()
      abortRef.current = null
    }
  }

  const onCancelGeneration = useCallback(() => {
    abortInFlight()
    setLoadingFalse()
  }, [abortInFlight, setLoadingFalse])

  // "Apply to current" is valid only when the visible graph was generated
  // for the app we'd be writing to. We require: a current app exists, its
  // mode matches the current modal mode, AND the last Generate (if any)
  // ran in this same mode — otherwise the user switched tabs mid-flight
  // and we'd be writing a workflow graph into a chatflow draft (or vice
  // versa). Falls back to "Create new app" only.
  const generatedMode = generatedModeRef.current
  const generatedModeMatches = generatedMode === null || generatedMode === mode
  const canApplyToCurrent = !!currentAppId && currentAppMode === mode && generatedModeMatches

  const handleApplyToNew = useCallback(async () => {
    if (!current?.graph || isApplying)
      return
    setApplyingTrue()
    try {
      const { appId, appMode } = await applyToNewApp({
        mode,
        graph: current.graph as GeneratedGraph,
        instruction,
        appName: current.app_name,
        icon: current.icon,
      })
      toast.success(t('workflowGenerator.applied'))
      closeGenerator()
      router.push(getRedirectionPath(isCurrentWorkspaceEditor, { id: appId, mode: appMode }))
    }
    catch (e: unknown) {
      if (e instanceof WorkflowApplyOrphanError) {
        // Sync failed AND we couldn't roll back. Route the user to /apps so
        // the orphan is still discoverable — they can delete it by hand.
        toast.error(t('workflowGenerator.errors.apply_failed_orphan'))
        closeGenerator()
        router.push('/apps')
        return
      }
      const message = e instanceof Error ? e.message : ''
      toast.error(message || t('workflowGenerator.applyFailed'))
    }
    finally {
      setApplyingFalse()
    }
  }, [current, instruction, mode, router, isCurrentWorkspaceEditor, closeGenerator, t, isApplying, setApplyingTrue, setApplyingFalse])

  const handleApplyToCurrentConfirmed = useCallback(async () => {
    if (!current?.graph || !currentAppId || isApplying)
      return
    hideConfirmOverwrite()
    setApplyingTrue()
    try {
      await applyToCurrentApp({ appId: currentAppId, graph: current.graph as GeneratedGraph })
      toast.success(t('workflowGenerator.applied'))
      closeGenerator()
      // Hard reload the workflow page so the canvas picks up the new draft —
      // ``router.refresh()`` only revalidates server-rendered route data, and
      // the Studio canvas is hydrated client-side via react-query / zustand.
      if (typeof window !== 'undefined')
        window.location.reload()
    }
    catch (e: unknown) {
      if (e instanceof WorkflowApplyHashCollisionError) {
        // Another tab edited the draft after we fetched it. Surface the
        // explanation + a one-click Reload via the toast's ``actionProps``
        // — the user needs an explicit affordance, but a non-blocking
        // toast is enough since they can also dismiss and copy the
        // generated graph manually before re-fetching.
        toast.error(t('workflowGenerator.errors.hash_collision_title'), {
          description: t('workflowGenerator.errors.hash_collision'),
          actionProps: {
            children: t('workflowGenerator.reload'),
            onClick: () => {
              if (typeof window !== 'undefined')
                window.location.reload()
            },
          },
        })
        return
      }
      const message = e instanceof Error ? e.message : ''
      toast.error(message || t('workflowGenerator.applyFailed'))
    }
    finally {
      setApplyingFalse()
    }
  }, [current, currentAppId, hideConfirmOverwrite, closeGenerator, t, isApplying, setApplyingTrue, setApplyingFalse])

  const modeLabel = mode === 'workflow' ? t('workflowGenerator.modes.workflow') : t('workflowGenerator.modes.chatflow')

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) {
          // Cancel any in-flight request BEFORE closing the store — a
          // request that resolves after the modal closes would still toast
          // against the now-unmounted modal and pollute version history.
          abortInFlight()
          closeGenerator()
        }
      }}
    >
      <DialogContent className="h-[min(680px,calc(100dvh-2rem))] max-h-none! w-[1140px] max-w-none! min-w-[1140px] overflow-hidden! border-none p-0! text-left align-middle">
        <div className="flex h-full min-h-0 flex-wrap">
          {/* Left pane: instructions + ideal output + model selector */}
          <div className="h-full w-[570px] shrink-0 overflow-y-auto border-r border-divider-regular p-6">
            <div className="mb-5">
              <div className="text-lg leading-[28px] font-bold text-text-primary">
                {t('workflowGenerator.title', { mode: modeLabel })}
              </div>
              <div className="mt-1 text-[13px] font-normal text-text-tertiary">
                {t('workflowGenerator.description')}
              </div>
            </div>

            <div>
              <ModelParameterModal
                popupClassName="w-[520px]!"
                isAdvancedMode={true}
                provider={model.provider}
                completionParams={model.completion_params}
                modelId={model.name}
                setModel={handleModelChange}
                onCompletionParamsChange={handleCompletionParamsChange}
                hideDebugWithMultipleModel
              />
            </div>

            <div className="mt-4">
              <div className="mb-1.5 system-sm-semibold-uppercase text-text-secondary">
                {t('workflowGenerator.instruction')}
              </div>
              <Textarea
                className="h-[160px]"
                placeholder={t('workflowGenerator.instructionPlaceholder')}
                value={instruction}
                onValueChange={setInstruction}
              />

              <ExamplePrompts mode={mode} onSelect={setInstruction} />

              <IdeaOutput
                value={ideaOutput}
                onChange={setIdeaOutput}
              />

              <div className="mt-7 flex justify-end space-x-2">
                <Button onClick={closeGenerator}>
                  {t('workflowGenerator.dismiss')}
                </Button>
                {isLoading
                  ? (
                      // Cancel surfaces the abort affordance during the 60 s
                      // window where the user might want to bail (slow
                      // model, wrong instruction, etc.). Hidden when idle so
                      // the row stays focused on the primary action.
                      <Button
                        className="flex space-x-1"
                        variant="secondary"
                        onClick={onCancelGeneration}
                      >
                        <span className="text-xs font-semibold">{t('workflowGenerator.cancel')}</span>
                      </Button>
                    )
                  : (
                      <Button
                        className="flex space-x-1"
                        variant="primary"
                        onClick={onGenerate}
                        disabled={!model.name}
                      >
                        <Generator className="size-4" />
                        <span className="text-xs font-semibold">{t('workflowGenerator.generate')}</span>
                      </Button>
                    )}
              </div>
            </div>
          </div>

          {/* Right pane: preview + version selector + apply */}
          {(!isLoading && current?.graph?.nodes?.length)
            ? (
                <div className="flex h-full w-0 grow flex-col bg-background-default-subtle p-6">
                  <div className="mb-3 flex items-center justify-between">
                    <VersionSelector
                      versionLen={versions?.length || 0}
                      value={currentVersionIndex || 0}
                      onChange={setCurrentVersionIndex}
                    />
                    <div className="flex items-center space-x-2">
                      {current?.graph && (
                        <RefineNode
                          mode={mode}
                          graph={current.graph as GeneratedGraph}
                          model={model ?? EMPTY_MODEL}
                          disabled={isApplying}
                          onRefined={addVersion}
                        />
                      )}
                      {canApplyToCurrent
                        ? (
                            // Studio button entry — overwrite the current draft
                            // is the only meaningful Apply action, so collapse
                            // the two buttons into one primary "Apply".
                            <Button
                              size="small"
                              variant="primary"
                              onClick={showConfirmOverwrite}
                              disabled={isApplying}
                            >
                              {t('workflowGenerator.studioApply')}
                            </Button>
                          )
                        : (
                            // cmd+k /create entry — no current-app context, so
                            // the only path is "Create new app".
                            <Button
                              size="small"
                              variant="primary"
                              onClick={handleApplyToNew}
                              disabled={isApplying}
                            >
                              {t('workflowGenerator.applyToNew')}
                            </Button>
                          )}
                    </div>
                  </div>
                  <div className="relative w-full grow overflow-hidden rounded-2xl border border-divider-subtle bg-background-default">
                    <WorkflowPreview
                      nodes={current.graph.nodes}
                      edges={current.graph.edges}
                      viewport={current.graph.viewport}
                      miniMapToRight
                    />
                  </div>
                  {current.message && (
                    <div className="mt-2 system-xs-regular text-text-tertiary">
                      {current.message}
                    </div>
                  )}
                </div>
              )
            : null}

          {isLoading && <GenerationPhases startedAt={startedAt} />}

          {!isLoading && !current?.graph?.nodes?.length && renderPlaceholder(t('workflowGenerator.placeholder'))}
        </div>

        <AlertDialog open={isShowConfirmOverwrite} onOpenChange={o => !o && hideConfirmOverwrite()}>
          <AlertDialogContent>
            <div className="flex flex-col gap-2 px-6 pt-6 pb-4">
              <AlertDialogTitle className="w-full truncate title-2xl-semi-bold text-text-primary">
                {t('workflowGenerator.overwriteTitle')}
              </AlertDialogTitle>
              <AlertDialogDescription className="w-full system-md-regular wrap-break-word whitespace-pre-wrap text-text-tertiary">
                {t('workflowGenerator.overwriteMessage')}
              </AlertDialogDescription>
            </div>
            <AlertDialogActions>
              <AlertDialogCancelButton>{t('operation.cancel', { ns: 'common' })}</AlertDialogCancelButton>
              <AlertDialogConfirmButton onClick={handleApplyToCurrentConfirmed}>
                {t('operation.confirm', { ns: 'common' })}
              </AlertDialogConfirmButton>
            </AlertDialogActions>
          </AlertDialogContent>
        </AlertDialog>
      </DialogContent>
    </Dialog>
  )
}

export default React.memo(WorkflowGeneratorModal)
