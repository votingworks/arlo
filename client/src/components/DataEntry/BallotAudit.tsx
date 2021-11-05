import React from 'react'
import { Formik, FormikProps, Field } from 'formik'
import styled from 'styled-components'
import { H3, Button, MenuItem } from '@blueprintjs/core'
import { ItemRenderer, ItemPredicate, Select } from '@blueprintjs/select'
import {
  BallotRow,
  ContestCard,
  ProgressActions,
  BlockCheckboxes,
  LeftCheckboxes,
  RightCheckboxes,
  CheckSelectCombo,
  SubTitle,
} from './Atoms'
import FormButton from '../Atoms/Form/FormButton'
import { IBallotInterpretation, Interpretation, IContest } from '../../types'
import FormField from '../Atoms/Form/FormField'
import BlockCheckbox from './BlockCheckbox'
import { IAuditSettings } from '../MultiJurisdictionAudit/useAuditSettings'

const NoteField = styled(Field)`
  textarea {
    height: 100px;
  }
`

const ContestTitle = styled(H3)`
  margin-bottom: 20px;
  font-weight: 500;
`

const SubmitButton = styled(FormButton)`
  border-radius: 5px;
  width: 12em;
  font-weight: 600;
  @media only screen and (max-width: 767px) {
    width: auto;
  }
`

interface IProps {
  contests: IContest[]
  auditSettings: IAuditSettings
  interpretations: IBallotInterpretation[]
  setInterpretations: (interpretations: IBallotInterpretation[]) => void
  previousBallot: () => void
  confirmSelections: (interpretations: IBallotInterpretation[]) => void
}

const BallotAudit: React.FC<IProps> = ({
  contests,
  auditSettings,
  interpretations,
  setInterpretations,
  confirmSelections,
  previousBallot,
}: IProps) => {
  return (
    <BallotRow>
      <div className="ballot-main">
        <SubTitle>Ballot Contests</SubTitle>
        <Formik
          initialValues={{ interpretations }}
          enableReinitialize
          onSubmit={values => {
            setInterpretations(values.interpretations)
            confirmSelections(values.interpretations)
          }}
        >
          {({
            handleSubmit,
            values,
            setFieldValue,
          }: FormikProps<{ interpretations: IBallotInterpretation[] }>) => {
            return (
              <form>
                {contests.map((contest, i) => (
                  <BallotAuditContest
                    key={`Contest ${contest.id}`}
                    contest={contest}
                    auditSettings={auditSettings}
                    interpretation={values.interpretations[i]}
                    setInterpretation={newInterpretation =>
                      setFieldValue(`interpretations[${i}]`, newInterpretation)
                    }
                  />
                ))}
                <ProgressActions>
                  <SubmitButton
                    type="submit"
                    onClick={handleSubmit}
                    intent="success"
                    large
                    disabled={
                      auditSettings.auditType === 'BALLOT_COMPARISON' &&
                      auditSettings.auditMathType === 'RAIRE'
                        ? !(
                            values.interpretations.filter(
                              ({ choiceIds }) =>
                                choiceIds.filter(choiceId => choiceId.rank)
                                  .length > 0
                            ).length === contests.length
                          )
                        : !(
                            values.interpretations.filter(
                              ({ interpretation }) => interpretation != null
                            ).length > 0
                          )
                    }
                  >
                    Submit Selections
                  </SubmitButton>
                  <Button onClick={previousBallot} intent="none">
                    Back
                  </Button>
                </ProgressActions>
              </form>
            )
          }}
        </Formik>
      </div>
    </BallotRow>
  )
}

interface IBallotAuditContestProps {
  contest: IContest
  interpretation: IBallotInterpretation
  auditSettings: IAuditSettings
  setInterpretation: (i: IBallotInterpretation) => void
}
interface IChoice {
  title: string
  rank: number
}

const BallotAuditContest = ({
  contest,
  auditSettings,
  interpretation,
  setInterpretation,
}: IBallotAuditContestProps) => {
  const onCheckboxClick = (value: string) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { checked } = e.currentTarget
    if (
      value === Interpretation.BLANK ||
      value === Interpretation.CANT_AGREE ||
      value === Interpretation.CONTEST_NOT_ON_BALLOT
    ) {
      setInterpretation({
        ...interpretation,
        interpretation: checked ? value : null,
        choiceIds: [],
      })
    } else {
      const choiceIds = checked
        ? [...interpretation.choiceIds, { id: value }]
        : interpretation.choiceIds.filter(v => v.id !== value)
      setInterpretation({
        ...interpretation,
        interpretation: choiceIds.length > 0 ? Interpretation.VOTE : null,
        choiceIds,
      })
    }
  }

  const ChoiceSelect = Select.ofType<IChoice>()
  const choiceItems = new Array(contest.choices.length)
    .fill('Choice')
    .map((item, idx) => ({ title: item, rank: idx + 1 }))
  const escapeRegExpChars = (text: string) => {
    // eslint-disable-next-line no-useless-escape
    return text.replace(/([.*+?^=!:${}()|\[\]\/\\])/g, '\\$1')
  }
  const highlightText = (text: string, query: string) => {
    let lastIndex = 0
    const words = query
      .split(/\s+/)
      .filter(word => word.length > 0)
      .map(escapeRegExpChars)
    if (words.length === 0) return [text]
    const regexp = new RegExp(words.join('|'), 'gi')
    const tokens: React.ReactNode[] = []
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const match = regexp.exec(text)
      if (!match) {
        break
      }
      const { length } = match[0]
      const before = text.slice(lastIndex, regexp.lastIndex - length)
      if (before.length > 0) {
        tokens.push(before)
      }
      // eslint-disable-next-line prefer-destructuring
      lastIndex = regexp.lastIndex
      tokens.push(<strong key={lastIndex}>{match[0]}</strong>)
    }
    const rest = text.slice(lastIndex)
    if (rest.length > 0) {
      tokens.push(rest)
    }
    return tokens
  }

  const renderChoice: ItemRenderer<IChoice> = (
    choice,
    { handleClick, modifiers, query }
  ) => {
    if (!modifiers.matchesPredicate) return null
    const text = `${choice.title} ${choice.rank}`
    return (
      <MenuItem
        active={modifiers.active}
        disabled={modifiers.disabled}
        key={`Dropdown Option ${choice.rank}`}
        onClick={handleClick}
        text={highlightText(text, query)}
      />
    )
  }
  const filterChoice: ItemPredicate<IChoice> = (query, choice) => {
    return (
      `${choice.title.toLowerCase()} ${choice.rank}`.indexOf(
        query.toLowerCase()
      ) >= 0
    )
  }
  const onSelectValueChange = (value: string) => (
    item: IChoice,
    e: React.SyntheticEvent<HTMLElement, Event> | undefined
  ) => {
    if (e) {
      const choiceIds =
        interpretation.choiceIds.filter(cId => cId.id === value).length > 0
          ? [
              ...interpretation.choiceIds.filter(v => v.id !== value),
              { id: value, rank: item.rank },
            ]
          : [...interpretation.choiceIds]
      setInterpretation({
        ...interpretation,
        interpretation: choiceIds.length > 0 ? Interpretation.VOTE : null,
        choiceIds,
      })
    }
  }

  const isVote = interpretation.interpretation === Interpretation.VOTE
  // To-do:
  // Fetch below values with proper API calls
  // Below values can be used for testing without API call
  // const auditType =
  //   contest.name === 'Contest 1' ? 'BALLOT_COMPARISON' : 'BALLOT_POLLING'
  // const auditMathType = contest.name === 'Contest 1' ? 'RAIRE' : 'SUPERSIMPLE'

  return (
    <ContestCard>
      <BlockCheckboxes>
        <LeftCheckboxes>
          <ContestTitle>{contest.name}</ContestTitle>
          {contest.choices.map(c => (
            <CheckSelectCombo key={`Candidate Choice: ${c.id}`}>
              <BlockCheckbox
                handleChange={onCheckboxClick(c.id)}
                checked={
                  isVote &&
                  interpretation.choiceIds.filter(
                    choiceId => choiceId.id === c.id
                  ).length > 0
                }
                label={c.name}
              />
              {/* TO DO: Change below condition to test based on above variables */}
              {auditSettings.auditType === 'BALLOT_COMPARISON' &&
                auditSettings.auditMathType === 'RAIRE' && (
                  <ChoiceSelect
                    items={choiceItems}
                    itemPredicate={filterChoice}
                    itemRenderer={renderChoice}
                    noResults={<MenuItem disabled text="No results." />}
                    onItemSelect={onSelectValueChange(c.id)}
                    disabled={
                      !(
                        interpretation.choiceIds.filter(
                          choiceId => choiceId.id === c.id
                        ).length > 0
                      )
                    }
                    fill
                  >
                    <Button
                      text={
                        interpretation.choiceIds.filter(
                          choiceId => choiceId.id === c.id && choiceId.rank
                        ).length > 0
                          ? `Choice ${
                              interpretation.choiceIds.filter(
                                choiceId => choiceId.id === c.id
                              )[0].rank
                            }`
                          : 'No Rank'
                      }
                      rightIcon="caret-down"
                      large
                    />
                  </ChoiceSelect>
                )}
            </CheckSelectCombo>
          ))}
        </LeftCheckboxes>
        <RightCheckboxes>
          <BlockCheckbox
            handleChange={onCheckboxClick(Interpretation.BLANK)}
            checked={interpretation.interpretation === Interpretation.BLANK}
            label="Blank vote"
            small
          />
          <BlockCheckbox
            handleChange={onCheckboxClick(Interpretation.CONTEST_NOT_ON_BALLOT)}
            checked={
              interpretation.interpretation ===
              Interpretation.CONTEST_NOT_ON_BALLOT
            }
            label="Not on Ballot"
            small
          />
          <NoteField
            name={`comment-${contest.name}`}
            type="textarea"
            component={FormField}
            value={interpretation.comment || ''}
            placeholder="Add Note"
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setInterpretation({
                ...interpretation,
                comment: e.currentTarget.value,
              })
            }
          />
        </RightCheckboxes>
      </BlockCheckboxes>
    </ContestCard>
  )
}

export default BallotAudit
