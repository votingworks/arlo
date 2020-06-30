import React, { useState, useEffect } from 'react'
import { useParams, useHistory } from 'react-router-dom'
import { H4, Callout, RadioGroup, Radio } from '@blueprintjs/core'
import { toast } from 'react-toastify'
import { Formik, FormikProps, Form, getIn, Field } from 'formik'
import FormButtonBar from '../../../Atoms/Form/FormButtonBar'
import FormButton from '../../../Atoms/Form/FormButton'
import { ISidebarMenuItem } from '../../../Atoms/Sidebar'
import H2Title from '../../../Atoms/H2Title'
import useAuditSettings from '../../useAuditSettings'
import useContests from '../../useContests'
import { IContest, ISampleSizeOption } from '../../../../types'
import useJurisdictions, { FileProcessingStatus } from '../../useJurisdictions'
import { api, checkAndToast, testNumber } from '../../../utilities'
import FormSection, {
  FormSectionDescription,
  FormSectionLabel,
} from '../../../Atoms/Form/FormSection'
import ContestsTable from './ContestsTable'
import SettingsTable from './SettingsTable'
import { isSetupComplete } from '../../StatusBox'
import useJurisdictionFile from '../Participants/useJurisdictionFile'
import ConfirmLaunch from './ConfirmLaunch'
import FormField from '../../../Atoms/Form/FormField'

const percentFormatter = new Intl.NumberFormat(undefined, {
  style: 'percent',
})

interface IStringSampleSize {
  size: string
  type: string | null
  prob: number | null
}

interface IProps {
  locked: boolean
  prevStage: ISidebarMenuItem
  refresh: () => void
}

const Review: React.FC<IProps> = ({ prevStage, locked, refresh }: IProps) => {
  const { electionId } = useParams<{ electionId: string }>()
  const [auditSettings] = useAuditSettings(electionId)
  const { electionName, randomSeed, riskLimit, online } = auditSettings
  const jurisdictions = useJurisdictions(electionId)
  const [jurisdictionFile] = useJurisdictionFile(electionId)
  const [contests] = useContests(electionId)
  const [sampleSizeOptions, setSampleSizeOptions] = useState<
    IStringSampleSize[]
  >([])
  const [sampleSize, setSampleSize] = useState('')
  const history = useHistory()
  const [isConfirmDialogOpen, setIsConfirmDialogOpen] = useState(false)

  useEffect(() => {
    ;(async () => {
      try {
        const { sampleSizes }: { sampleSizes: ISampleSizeOption[] } = await api(
          `/election/${electionId}/sample-sizes`
        )
        setSampleSizeOptions(
          sampleSizes.map(v => ({
            ...v,
            size: `${v.size}`,
          }))
        )
      } catch (err) /* istanbul ignore next */ {
        // TEST TODO
        toast.error(err.message)
      }
    })()
  }, [electionId])

  const submit = async () => {
    try {
      const result = await api(`/election/${electionId}/round`, {
        method: 'POST',
        body: JSON.stringify({
          sampleSize: Number(sampleSize),
          roundNum: 1,
        }),
        headers: {
          'Content-Type': 'application/json',
        },
      })
      // checkAndToast left here for consistency and reference but not tested since it's vestigial
      /* istanbul ignore next */
      if (checkAndToast(result)) {
        return
      }
      refresh()
      history.push(`/election/${electionId}/progress`)
    } catch (err) /* istanbul ignore next */ {
      // TEST TODO
      toast.error(err.message)
    }
  }

  if (!contests) return null // Still loading

  const targetedContests = contests
    .filter(c => c.isTargeted === true)
    .map(c => ({
      ...c,
      jurisdictionIds: c.jurisdictionIds.map(j =>
        jurisdictions.length > 0
          ? jurisdictions.find(p => p.id === j)!.name
          : ''
      ),
    }))
  const opportunisticContests = contests
    .filter(c => c.isTargeted === false)
    .map(c => ({
      ...c,
      jurisdictionIds: c.jurisdictionIds.map(j =>
        jurisdictions.length > 0
          ? jurisdictions.find(p => p.id === j)!.name
          : ''
      ),
    }))

  const completedBallotUploads = jurisdictions.filter(
    j =>
      j.ballotManifest.processing &&
      j.ballotManifest.processing.status === FileProcessingStatus.PROCESSED
  ).length

  return (
    <div>
      <H2Title>Review &amp; Launch</H2Title>
      <Callout intent="warning">
        Once the audit is started, the audit definition will no longer be
        editable. Please make sure this data is correct before launching the
        audit.
      </Callout>
      <br />
      <H4>Audit Settings</H4>
      <SettingsTable>
        <tbody>
          <tr>
            <td>Election Name:</td>
            <td>{electionName}</td>
          </tr>
          <tr>
            <td>Risk Limit:</td>
            <td>{riskLimit}</td>
          </tr>
          <tr>
            <td>Random Seed:</td>
            <td>{randomSeed}</td>
          </tr>
          <tr>
            <td>Participating Jurisdictions:</td>
            <td>
              <a
                href={`/api/election/${electionId}/jurisdiction/file/csv`}
                target="_blank"
                rel="noopener noreferrer"
              >
                {jurisdictionFile && jurisdictionFile.file
                  ? jurisdictionFile.file.name
                  : ''}
              </a>
            </td>
          </tr>
          <tr>
            <td>Audit Board Data Entry:</td>
            <td>{online ? 'Online' : 'Offline'}</td>
          </tr>
        </tbody>
      </SettingsTable>
      <ContestsTable>
        <thead>
          <tr>
            <th>Target Contests</th>
            <th>Jurisdictions</th>
          </tr>
        </thead>
        <tbody>
          {targetedContests.map((c: IContest) => (
            <tr key={c.id}>
              <td>{c.name}</td>
              <td>{c.jurisdictionIds.join(', ')}</td>
            </tr>
          ))}
        </tbody>
      </ContestsTable>
      <ContestsTable>
        <thead>
          <tr>
            <th>Opportunistic Contests</th>
            <th>Jurisdictions</th>
          </tr>
        </thead>
        <tbody>
          {opportunisticContests.map((c: IContest) => (
            <tr key={c.id}>
              <td>{c.name}</td>
              <td>{c.jurisdictionIds.join(', ')}</td>
            </tr>
          ))}
        </tbody>
      </ContestsTable>
      <H4>Sample Size Options</H4>
      <Formik
        initialValues={{
          sampleSize: sampleSizeOptions.length ? sampleSizeOptions[0].size : '',
          customSampleSize: '',
        }}
        enableReinitialize
        onSubmit={v => {
          if (v.sampleSize === 'custom') {
            setSampleSize(v.customSampleSize)
          } else {
            setSampleSize(v.sampleSize)
          }
          setIsConfirmDialogOpen(true)
        }}
      >
        {({
          values,
          handleSubmit,
          setFieldValue,
        }: FormikProps<{ sampleSize: string }>) => (
          <Form data-testid="sample-size-form">
            {sampleSizeOptions.length && (
              <FormSection>
                <FormSectionLabel>Estimated Sample Size</FormSectionLabel>
                <FormSectionDescription>
                  Choose the initial sample size for each contest you would like
                  to use for Round 1 of the audit from the options below.
                </FormSectionDescription>
                <FormSectionDescription>
                  <RadioGroup
                    name="sampleSize"
                    onChange={e =>
                      setFieldValue('sampleSize', e.currentTarget.value)
                    }
                    selectedValue={getIn(values, 'sampleSize')}
                    disabled={locked}
                  >
                    {sampleSizeOptions.map((option: ISampleSizeOption) => {
                      return (
                        <Radio value={option.size} key={option.size}>
                          {option.type ? 'BRAVO Average Sample Number: ' : ''}
                          {`${option.size} samples`}
                          {option.prob
                            ? ` (${percentFormatter.format(
                                option.prob
                              )} chance of reaching risk limit and completing the audit in one round)`
                            : ''}
                        </Radio>
                      )
                    })}
                    <Radio value="custom">
                      Enter your own sample size (not recommended)
                    </Radio>
                    {getIn(values, 'sampleSize') === 'custom' && (
                      <Field
                        component={FormField}
                        name="customSampleSize"
                        type="text"
                        validate={testNumber(
                          Number(targetedContests[0].totalBallotsCast),
                          'Must be less than or equal to the total number of ballots in targeted contests'
                        )}
                      />
                    )}
                  </RadioGroup>
                </FormSectionDescription>
              </FormSection>
            )}
            <FormButtonBar>
              <FormButton onClick={prevStage.activate}>Back</FormButton>
              <FormButton
                intent="primary"
                disabled={
                  locked ||
                  !isSetupComplete(jurisdictions, contests, auditSettings)
                }
                onClick={handleSubmit}
              >
                Launch Audit
              </FormButton>
            </FormButtonBar>
          </Form>
        )}
      </Formik>
      <ConfirmLaunch
        isOpen={isConfirmDialogOpen}
        handleClose={() => setIsConfirmDialogOpen(false)}
        onLaunch={submit}
        numJurisdictions={jurisdictions.length}
        completedBallotUploads={completedBallotUploads}
      />
    </div>
  )
}

export default Review
