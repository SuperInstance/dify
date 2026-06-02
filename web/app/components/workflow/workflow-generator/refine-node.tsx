'use client'

import type { GeneratedGraph, GenerateWorkflowResponse, WorkflowGeneratorMode } from './types'
import type { Model } from '@/types/app'
import { Button } from '@langgenius/dify-ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@langgenius/dify-ui/popover'
import { Textarea } from '@langgenius/dify-ui/textarea'
import { toast } from '@langgenius/dify-ui/toast'
import { useBoolean } from 'ahooks'
import { useCallback, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { regenerateWorkflowNode } from '@/service/debug'

type Props = {
  mode: WorkflowGeneratorMode
  graph: GeneratedGraph
  model: Model
  disabled?: boolean
  /**
   * Called with the API response when refinement succeeds. The caller is
   * responsible for appending it to the version history; this component
   * stays stateless beyond its own form fields so reopening the popover
   * doesn't carry state between refinements.
   */
  onRefined: (response: GenerateWorkflowResponse) => void
}

/**
 * "Refine a node" affordance: anchored next to the Apply buttons, opens a
 * popover with a node-picker + refinement textarea. Submitting calls
 * ``/workflow-generate-node`` with the current graph and hands the result
 * to ``onRefined`` so the parent can splice it into version history.
 *
 * Stateless across opens — closing the popover (or successful refinement)
 * resets the form so the next refinement starts clean.
 */
const RefineNode = ({ mode, graph, model, disabled, onRefined }: Props) => {
  const { t } = useTranslation('workflow')
  const [open, { setTrue: openPopover, setFalse: closePopover, toggle: togglePopover }] = useBoolean(false)
  const [nodeId, setNodeId] = useState('')
  const [refinement, setRefinement] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Build a flat option list — id + title — from the current graph. Excludes
  // container *start* helpers (custom-iteration-start / custom-loop-start)
  // since refining those is meaningless; they're auto-generated wrappers.
  const nodeOptions = useMemo(() => {
    return (graph.nodes ?? [])
      .filter((n) => {
        const innerType = (n.data as { type?: string } | undefined)?.type ?? ''
        return innerType !== 'iteration-start' && innerType !== 'loop-start'
      })
      .map((n) => {
        const data = n.data as { title?: string, type?: string } | undefined
        const label = data?.title || data?.type || n.id
        return { id: n.id, label: `${label} (${n.id})` }
      })
  }, [graph.nodes])

  const reset = useCallback(() => {
    setNodeId('')
    setRefinement('')
  }, [])

  const handleOpenChange = useCallback((next: boolean) => {
    if (next) {
      openPopover()
    }
    else {
      closePopover()
      reset()
    }
  }, [openPopover, closePopover, reset])

  const handleSubmit = useCallback(async () => {
    if (!nodeId) {
      toast.error(t('workflowGenerator.refine.nodeRequired'))
      return
    }
    if (!refinement.trim()) {
      toast.error(t('workflowGenerator.refine.refinementRequired'))
      return
    }
    if (!model.name) {
      toast.error(t('workflowGenerator.modelRequired'))
      return
    }

    setSubmitting(true)
    try {
      const res = await regenerateWorkflowNode({
        mode,
        graph,
        node_id: nodeId,
        refinement: refinement.trim(),
        model_config: model,
      })
      const first = res.errors?.[0]
      if (first) {
        const i18nKey = `workflowGenerator.errors.${first.code}`
        const localised = t(i18nKey, { defaultValue: '' })
        toast.error(localised || first.detail || res.error || t('workflowGenerator.refine.failed'))
        return
      }
      if (res.error) {
        toast.error(res.error)
        return
      }
      onRefined(res)
      handleOpenChange(false)
      toast.success(t('workflowGenerator.refine.applied'))
    }
    catch (e) {
      const message = e instanceof Error ? e.message : ''
      toast.error(message || t('workflowGenerator.refine.failed'))
    }
    finally {
      setSubmitting(false)
    }
  }, [nodeId, refinement, model, mode, graph, t, onRefined, handleOpenChange])

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger>
        <Button
          size="small"
          variant="secondary"
          disabled={disabled || nodeOptions.length === 0}
          onClick={togglePopover}
        >
          {t('workflowGenerator.refine.button')}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[360px] p-4" placement="bottom-end">
        <div className="mb-2 system-sm-semibold-uppercase text-text-secondary">
          {t('workflowGenerator.refine.title')}
        </div>
        <div className="mb-3">
          <label className="mb-1 block system-xs-medium text-text-tertiary">
            {t('workflowGenerator.refine.nodeLabel')}
          </label>
          <select
            className="w-full rounded-md border border-divider-regular bg-background-default px-2 py-1.5 text-sm text-text-primary"
            value={nodeId}
            onChange={e => setNodeId(e.target.value)}
          >
            <option value="">{t('workflowGenerator.refine.nodePlaceholder')}</option>
            {nodeOptions.map(opt => (
              <option key={opt.id} value={opt.id}>{opt.label}</option>
            ))}
          </select>
        </div>
        <div className="mb-3">
          <label className="mb-1 block system-xs-medium text-text-tertiary">
            {t('workflowGenerator.refine.refinementLabel')}
          </label>
          <Textarea
            className="h-[100px]"
            placeholder={t('workflowGenerator.refine.refinementPlaceholder')}
            value={refinement}
            onValueChange={setRefinement}
          />
        </div>
        <div className="flex justify-end space-x-2">
          <Button size="small" variant="secondary" onClick={() => handleOpenChange(false)}>
            {t('workflowGenerator.dismiss')}
          </Button>
          <Button size="small" variant="primary" onClick={handleSubmit} disabled={submitting}>
            {submitting ? t('workflowGenerator.refine.submitting') : t('workflowGenerator.refine.submit')}
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  )
}

export default RefineNode
