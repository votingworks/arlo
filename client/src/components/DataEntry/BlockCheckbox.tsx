import React from 'react'
import styled from 'styled-components'
import { Colors } from '@blueprintjs/core'

const Block = styled.label`
  width: 100%;

  &.bp3-control.bp3-checkbox {
    display: inline-block;
    position: relative;
    margin-right: 20px;
    margin-bottom: 10px;
    padding-left: 0;

    .checkbox-text {
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      width: 100%;
      padding: 5px;
      text-align: center;
    }

    .bp3-control-indicator {
      margin-left: 0;
      border: 1px solid ${Colors.GRAY4};
      border-radius: 10px;
      background-color: ${Colors.WHITE};
      width: 100%;
      height: 2.5em;
      color: ${Colors.BLACK};

      &::before {
        display: none;
      }

      &.small {
        height: 2em;
      }
    }

    input:checked ~ .bp3-control-indicator,
    &:hover .bp3-control-indicator {
      background-color: ${Colors.BLUE3};
      background-image: none;
      color: #ffffff;
    }
  }
`

interface IProps {
  label: string
  handleChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
  locked?: boolean
  checked?: boolean
  small?: boolean
}

const BlockCheckbox = ({ label, handleChange, small, checked }: IProps) => (
  <Block className="bp3-control bp3-checkbox">
    <input type="checkbox" onChange={handleChange} checked={checked} />
    <span className={`${small && 'small'} bp3-control-indicator`}>
      <span className="checkbox-text">{label}</span>
    </span>
  </Block>
)

export default BlockCheckbox
