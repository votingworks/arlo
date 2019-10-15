import React from 'react'
import styled from 'styled-components'
import { IBallot } from '../../types'
import FormButton from '../Form/FormButton'

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

const LockedButton = styled(FormButton)`
  text-align: center;
`

interface IProps {
  name?: string
  value: Exclude<IBallot['vote'], null>
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
} as const

export type voteKey = keyof typeof TEXT
export type voteValue = typeof TEXT[voteKey]

const BlockRadio = ({
  name = '',
  value,
  handleChange,
  locked,
  className,
  checked,
}: IProps) => (
  <>
    {locked ? (
      <LockedButton disabled fill large intent="primary">
        {TEXT[value]}
      </LockedButton>
    ) : (
      <Block className={`${className} bp3-control bp3-radio`}>
        <input
          type="radio"
          name={name}
          data-testid={value}
          value={value}
          onChange={handleChange}
          checked={checked}
        />
        <span className="bp3-control-indicator">
          <span className="radio-text">{TEXT[value]}</span>
        </span>
      </Block>
    )}
  </>
)

export default BlockRadio
