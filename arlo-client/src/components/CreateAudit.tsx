import React, { useState } from 'react'
import styled from 'styled-components'
import FormButton from './Form/FormButton'
import api from './utilities'

const Button = styled(FormButton)`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  height: 2.5rem;
  padding: 0 30px;
  font-size: 1.5rem;
`

const CreateAudit = ({ history }: any) => {
  const [loading, setLoading] = useState(false)
  const onClick = async () => {
    setLoading(true)
    const { electionId } = await api('/election/new', { method: 'POST' })
    history.push(`/election/${electionId}`)
  }
  return (
    <Button type="button" onClick={onClick}>
      {loading ? 'Wait a moment...' : 'Create a New Audit'}
    </Button>
  )
}

export default CreateAudit
