import React from 'react'
import styled from 'styled-components'
import FormButton from './Form/FormButton'

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
  const onClick = () => {
    history.push('/election/1')
  }
  return (
    <Button type="button" onClick={onClick}>
      Create a New Audit
    </Button>
  )
}

export default CreateAudit
