import React from 'react'

const CreateAudit = ({ history }: any) => {
  const onClick = () => {
    history.push('/election/1')
  }
  return (
    <button type="button" onClick={onClick}>
      Create a New Audit
    </button>
  )
}

export default CreateAudit
