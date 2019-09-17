import React from 'react'
import styled from 'styled-components'
import { Ballot } from '../../types'

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
  name?: string
  value: Ballot['vote']
  handleChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
  locked?: boolean
  className?: string
  checked?: boolean
}

const TEXT = {
  YES: 'Yes/For',
  NO: 'No/Against',
  NO_CONSENSUS: 'No audit board consensus',
  NO_VOTE: 'Blank vote/no mark',
}

const BlockRadio = ({
  name = '',
  value,
  handleChange = () => {},
  locked,
  className,
  checked,
}: Props) => (
  <Block className={`${className} bp3-control bp3-radio`}>
    {locked ? (
      <input
        type="radio"
        name={name}
        value={value || undefined}
        onChange={handleChange}
        disabled
        checked
      />
    ) : (
      <input
        type="radio"
        name={name}
        value={value || undefined}
        onChange={handleChange}
        checked={checked}
      />
    )}
    <span className="bp3-control-indicator">
      <span className="radio-text">{value ? TEXT[value] : ''}</span>
    </span>
  </Block>
)

export default BlockRadio
