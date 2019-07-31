import React, { useState } from 'react'
import styled from 'styled-components'
import FormButton from './Form/FormButton'
//import api from './utilities'

const Button = styled(FormButton)`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 50%;
  height: 100px;
  font-size: 40px;
`

const CreateAudit = ({ history }: any) => {
  const [loading, setLoading] = useState(false)
  const onClick = async () => {
    setLoading(true)
    //const { id } = await api('/new-audit', {method: 'POST'})
    const id = 1
    history.push(`/election/${id}`)
  }
  return (
    <Button type="button" onClick={onClick}>
      {loading ? 'Wait a moment...' : 'Create a New Audit'}
    </Button>
  )
}

export default CreateAudit
