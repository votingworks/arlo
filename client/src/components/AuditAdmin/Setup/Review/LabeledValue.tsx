import React from 'react'

interface IProps {
  label: string
  children: React.ReactNode
}

const LabeledValue: React.FC<IProps> = ({ label, children }) => (
  <div>
    <label className="bp3-text-small" style={{ fontWeight: 'bold' }}>
      {label}
    </label>
    <div className="bp3-text-large">{children}</div>
  </div>
)

export default LabeledValue
