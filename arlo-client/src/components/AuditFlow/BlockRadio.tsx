import React from 'react'
import styled from 'styled-components'

const Block = styled.label`
  &.bp3-control.bp3-radio {
    display: inline-block;
    position: relative;
    margin-bottom: 20px;

    .bp3-control-indicator {
      border-radius: unset;
      width: 10em;
      height: 3em;

      &::before {
        display: none;
      }
      .radio-text {
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        width: 100%;
        padding: 5px;
        text-align: center;
      }
    }
  }
`

interface Props {
  name: string
  value: string
  children: React.ReactNode
  handleChange: (e: React.ChangeEvent<HTMLInputElement>) => void
}

const BlockRadio = ({ name, value, children, handleChange }: Props) => (
  <Block className="bp3-control bp3-radio">
    <input type="radio" name={name} value={value} onChange={handleChange} />
    <span className="bp3-control-indicator">
      <span className="radio-text">{children}</span>
    </span>
  </Block>
)

export default BlockRadio
