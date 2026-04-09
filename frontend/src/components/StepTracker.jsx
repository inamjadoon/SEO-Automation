import React from 'react'
import '../styles/StepTracker.css'

const STEPS = [
  { id: 'registered', label: 'Site registered in database' },
  { id: 'crawling',   label: 'Crawling your website' },
  { id: 'faq',        label: 'Generating FAQ schema' },
  { id: 'jsonld',     label: 'Building JSON-LD structured data' },
  { id: 'snippet',    label: 'Preparing Squarespace snippet' },
]

export { STEPS }

export default function StepTracker({ currentStep }) {
  return (
    <div className="step-tracker">
      {STEPS.map((step, index) => {
        const isDone    = index < currentStep
        const isCurrent = index === currentStep
        

        const stateClass = isDone ? 'is-done' : isCurrent ? 'is-current' : 'is-pending'
        const circleClass = isDone ? 'done' : isCurrent ? 'current' : 'pending'
        const statusClass = isDone ? 'done' : isCurrent ? 'current' : 'pending'
        const statusText  = isDone ? 'Done' : isCurrent ? 'In progress…' : 'Pending'

        return (
          <div key={step.id} className={`step-row ${stateClass}`}>
            <div className={`step-circle ${circleClass}`}>
              {isDone ? '✓' : index + 1}
            </div>

            <div className="step-content">
              <span className="step-label">{step.label}</span>
              <span className={`step-status ${statusClass}`}>{statusText}</span>
            </div>

            {isCurrent && <div className="step-spinner" />}
          </div>
        )
      })}
    </div>
  )
}