import React from 'react'
import styled from 'styled-components'

const Block = styled.label`
  &.bp3-control.bp3-checkbox {
    display: inline-block;
    position: relative;
    margin-right: 20px;
    margin-bottom: 20px;

    .bp3-control-indicator {
      border-radius: unset;
      width: 10em;
      height: 3em;

      &::before {
        display: none;
      }
      .checkbox-text {
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        width: 100%;
        padding: 5px;
        text-align: center;
      }

      &.gray {
        background-color: #dddddd;
      }
    }
  }
`

interface IProps {
  name: string
  value: string
  label: string
  handleChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
  locked?: boolean
  className?: string
  checked?: boolean
  gray?: boolean
}

const BlockCheckbox = ({
  name,
  value,
  label,
  handleChange,
  className,
  gray,
  checked,
}: IProps) => (
  <Block className={`${className || ''} bp3-control bp3-checkbox`}>
    <input
      type="checkbox"
      name={name}
      data-testid={value}
      value={value}
      onChange={handleChange}
      checked={checked}
    />
    <span className={`${gray && !checked && 'gray'} bp3-control-indicator`}>
      <span className="checkbox-text">{label}</span>
    </span>
  </Block>
)

export default BlockCheckbox
