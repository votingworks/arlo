import React from 'react'
import styled from 'styled-components'
import { InputGroup, NumericInput } from '@blueprintjs/core'
import { getIn } from 'formik'

const Wrapper = styled.div`
  width: 45%;
`

const Field = styled(InputGroup)`
  width: 100%;
`

const NumberField = styled(NumericInput)`
  width: 100%;
`

const ErrorLabel = styled.p`
  width: 100%;
  color: #ff0000;
  font-size: 10px;
`

interface Props {
  field?: any
  form?: any
  disabled?: boolean
  value?: string | number
  onChange?: (e: React.ChangeEvent<any>) => void
  onBlur?: (e: any) => void
  name?: string
  type?: string
  error?: string
  touched?: boolean
  className?: string
}

const FormField = ({
  field,
  form: { touched, errors },
  disabled,
  className,
  ...rest
}: Props) => (
  <Wrapper className={className}>
    {rest.type === 'number' ? (
      <NumberField disabled={disabled} {...field} {...rest} />
    ) : (
      <Field disabled={disabled} {...field} {...rest} />
    )}
    {getIn(errors, field.name) && getIn(touched, field.name) && (
      <ErrorLabel data-testid={`${field.name}-error`}>
        {getIn(errors, field.name)}
      </ErrorLabel>
    )}
  </Wrapper>
)

export default FormField
