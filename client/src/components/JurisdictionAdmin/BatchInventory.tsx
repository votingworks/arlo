import React, { useState } from 'react'
import { H2, Button, H4, Colors, Icon, Checkbox, Card } from '@blueprintjs/core'
import {
  useQueryClient,
  useMutation,
  useQuery,
  UseQueryResult,
  UseMutationResult,
} from 'react-query'
import styled from 'styled-components'
import { useParams, Link } from 'react-router-dom'
import { Wrapper, Inner } from '../Atoms/Wrapper'
import FileUpload from '../Atoms/FileUpload'
import { fetchApi } from '../../utils/api'
import AsyncButton from '../Atoms/AsyncButton'
import { FileProcessingStatus } from '../useCSV'
import {
  IFileUpload,
  useUploadFiles,
  useDeleteFile,
  useUploadedFile,
} from '../useFileUpload'
import { apiDownload } from '../utilities'
import LinkButton from '../Atoms/LinkButton'

const STEPS = [
  'Upload Election Results',
  'Inventory Batches',
  'Download Audit Files',
] as const

const isUploaded = (fileUpload: IFileUpload) =>
  fileUpload.uploadedFile.data?.processing?.status ===
  FileProcessingStatus.PROCESSED

const useBatchInventoryCVR = (
  electionId: string,
  jurisdictionId: string
): IFileUpload => {
  const key = ['batchInventory', jurisdictionId, 'cvr']
  const url = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/cvr`
  const uploadFiles = useUploadFiles(key, url)
  const deleteFile = useDeleteFile(key, url)
  const queryClient = useQueryClient()
  return {
    uploadedFile: useUploadedFile(key, url, {
      onFileChange: () =>
        // Tabulator status file is reprocessed when CVR is uploaded
        queryClient.invalidateQueries([
          'batchInventory',
          jurisdictionId,
          'tabulatorStatus',
        ]),
    }),
    uploadFiles: files => {
      const formData = new FormData()
      formData.append('cvr', files[0], files[0].name)
      return uploadFiles.mutateAsync(formData)
    },
    uploadProgress: uploadFiles.progress,
    deleteFile: () => deleteFile.mutateAsync(),
    downloadFileUrl: `${url}/file`,
  }
}

const useBatchInventoryTabulatorStatus = (
  electionId: string,
  jurisdictionId: string
): IFileUpload => {
  const key = ['batchInventory', jurisdictionId, 'tabulatorStatus']
  const url = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/tabulator-status`
  const uploadFiles = useUploadFiles(key, url)
  const deleteFile = useDeleteFile(key, url)
  return {
    uploadedFile: useUploadedFile(key, url),
    uploadFiles: files => {
      const formData = new FormData()
      formData.append('tabulatorStatus', files[0], files[0].name)
      return uploadFiles.mutateAsync(formData)
    },
    uploadProgress: uploadFiles.progress,
    deleteFile: () => deleteFile.mutateAsync(),
    downloadFileUrl: `${url}/file`,
  }
}

interface ISignOffQueries {
  status: UseQueryResult<{ signedOffAt: string | null }>
  signOff: UseMutationResult<void, unknown, void, unknown>
  undoSignOff: UseMutationResult<void, unknown, void, unknown>
}

const useBatchInventorySignOff = (
  electionId: string,
  jurisdictionId: string
): ISignOffQueries => {
  const queryClient = useQueryClient()
  const key = ['batchInventory', jurisdictionId, 'signOff']
  const url = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/sign-off`
  const status = useQuery<{ signedOffAt: string | null }>(key, () =>
    fetchApi(url)
  )
  const signOff = useMutation(() => fetchApi(url, { method: 'POST' }), {
    onSuccess: () => queryClient.invalidateQueries(key),
  })
  const undoSignOff = useMutation(() => fetchApi(url, { method: 'DELETE' }), {
    onSuccess: () => queryClient.invalidateQueries(key),
  })
  return {
    status,
    signOff,
    undoSignOff,
  }
}

const StepContainer = styled(Card).attrs({ elevation: 1 })`
  padding: 0;
`

const StepProgressRow = styled.ol`
  background-color: ${Colors.LIGHT_GRAY5};
  display: flex;
  align-items: center;
  padding: 25px;
  margin: 0;
  border-radius: 3px 3px 0 0;
`

const StepProgressStep = styled.li`
  display: flex;
  align-items: center;
`

const StepProgressCircle = styled.div<{ incomplete: boolean }>`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 30px;
  width: 30px;
  border-radius: 50%;
  background-color: ${props =>
    props.incomplete ? Colors.GRAY4 : Colors.BLUE3};
  margin-right: 10px;
  color: ${Colors.WHITE};
  font-weight: 500;
`

const StepProgressLabel = styled.div<{ incomplete: boolean }>`
  color: ${props => (props.incomplete ? Colors.GRAY3 : 'inherit')};
  font-weight: 700;
`

const StepProgressLine = styled.div`
  flex-grow: 1;
  height: 1px;
  background: ${Colors.GRAY5};
  margin: 0 10px;
`

const StepProgress: React.FC<{
  steps: readonly string[]
  currentStep: string
}> = ({ steps, currentStep }) => {
  const currentStepIndex = steps.indexOf(currentStep)
  return (
    <StepProgressRow>
      {steps.map((step, i) => (
        <React.Fragment key={step}>
          <StepProgressStep
            aria-label={step}
            aria-current={i === currentStepIndex ? 'step' : undefined}
          >
            <StepProgressCircle incomplete={i > currentStepIndex}>
              {i < currentStepIndex ? <Icon icon="tick" /> : i + 1}
            </StepProgressCircle>
            <StepProgressLabel incomplete={i > currentStepIndex}>
              {step}
            </StepProgressLabel>
          </StepProgressStep>
          {i < steps.length - 1 && <StepProgressLine />}
        </React.Fragment>
      ))}
    </StepProgressRow>
  )
}

const StepPanel = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 70px;
  min-height: 300px;
  padding: 50px 70px;
  > * {
    flex: 1;
  }
`

const StepActionsRow = styled.div`
  display: flex;
  padding: 20px;
  background-color: ${Colors.LIGHT_GRAY5};
  justify-content: space-between;
  border-radius: 0 0 3px 3px;
`

const StepActions: React.FC<{
  left?: React.ReactElement
  right?: React.ReactElement
}> = ({ left, right }) => (
  <StepActionsRow>
    {left || <div />}
    {right || <div />}
  </StepActionsRow>
)

const UploadElectionResultsStep: React.FC<{
  nextStep: () => void
  cvrUpload: IFileUpload
  tabulatorStatusUpload: IFileUpload
}> = ({ nextStep, cvrUpload, tabulatorStatusUpload }) => {
  return (
    <>
      <StepPanel>
        <FileUpload
          title="Cast Vote Records (CVR)"
          {...cvrUpload}
          acceptFileTypes={['csv']}
        />
        <FileUpload
          title="Tabulator Status"
          {...tabulatorStatusUpload}
          acceptFileTypes={['xml']}
          uploadDisabled={!isUploaded(cvrUpload)}
        />
      </StepPanel>
      <StepActions
        right={
          <Button
            onClick={nextStep}
            intent="primary"
            disabled={
              !(isUploaded(cvrUpload) && isUploaded(tabulatorStatusUpload))
            }
            rightIcon="chevron-right"
          >
            Continue
          </Button>
        }
      />
    </>
  )
}

const InventoryBatchesStep: React.FC<{
  worksheetUrl: string
  signOffQueries: ISignOffQueries
  prevStep: () => void
  nextStep: () => void
}> = ({ prevStep, nextStep, signOffQueries, worksheetUrl }) => {
  if (!signOffQueries.status.isSuccess) return null

  const isSignedOff = signOffQueries.status.data.signedOffAt !== null

  const onSignOffToggle = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (event.target.checked) {
      await signOffQueries.signOff.mutateAsync()
    } else {
      await signOffQueries.undoSignOff.mutateAsync()
    }
  }

  return (
    <>
      <StepPanel>
        <div style={{ textAlign: 'center' }}>
          <p>
            Follow the instructions in the worksheet to inventory your batches.
          </p>
          <p>
            <AsyncButton
              intent="primary"
              large
              icon="download"
              onClick={() => apiDownload(worksheetUrl)}
            >
              Download Batch Inventory Worksheet
            </AsyncButton>
          </p>
          <br />
          <p>
            <Checkbox large onChange={onSignOffToggle} checked={isSignedOff}>
              <span>I have completed the batch inventory worksheet.</span>
            </Checkbox>
          </p>
        </div>
      </StepPanel>
      <StepActions
        left={
          <Button icon="chevron-left" onClick={prevStep}>
            Back
          </Button>
        }
        right={
          <Button
            disabled={!isSignedOff}
            onClick={nextStep}
            intent="primary"
            rightIcon="chevron-right"
            style={{ marginLeft: '10px' }}
          >
            Continue
          </Button>
        }
      />
    </>
  )
}

const DownloadAuditFilesStep: React.FC<{
  ballotManifestUrl: string
  batchTalliesUrl: string
  prevStep: () => void
}> = ({ ballotManifestUrl, batchTalliesUrl, prevStep }) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()
  return (
    <>
      <StepPanel>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            maxWidth: '50%',
          }}
        >
          <H4>Batch Inventory Complete</H4>
          <p style={{ marginBottom: '15px' }}>
            Next, download the Ballot Manifest and Candidate Totals by Batch
            files, then upload them on the{' '}
            <Link to={`/election/${electionId}/jurisdiction/${jurisdictionId}`}>
              Audit Source Data
            </Link>{' '}
            page.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <AsyncButton
              intent="primary"
              large
              icon="download"
              onClick={() => apiDownload(ballotManifestUrl)}
            >
              Download Ballot Manifest
            </AsyncButton>
            <AsyncButton
              intent="primary"
              large
              icon="download"
              onClick={() => apiDownload(batchTalliesUrl)}
              style={{ marginTop: '10px' }}
            >
              Download Candidate Totals by Batch
            </AsyncButton>
          </div>
        </div>
      </StepPanel>
      <StepActions
        left={
          <Button icon="chevron-left" onClick={prevStep}>
            Back
          </Button>
        }
        right={
          <LinkButton
            to={`/election/${electionId}/jurisdiction/${jurisdictionId}`}
            intent="primary"
            rightIcon="chevron-right"
          >
            Return to Audit Source Data
          </LinkButton>
        }
      />
    </>
  )
}

const HeadingRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
`

const BatchInventorySteps: React.FC<{
  cvrUpload: IFileUpload
  tabulatorStatusUpload: IFileUpload
  signOffQueries: ISignOffQueries
}> = ({ cvrUpload, tabulatorStatusUpload, signOffQueries }) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()

  // Start on the step that's most relevant given progress so far (e.g. if the
  // user left and came back)
  const areFilesUploaded =
    isUploaded(cvrUpload) && isUploaded(tabulatorStatusUpload)
  const isSignedOff = signOffQueries.status.data?.signedOffAt !== null
  const initialStep = !areFilesUploaded
    ? 'Upload Election Results'
    : !isSignedOff
    ? 'Inventory Batches'
    : 'Download Audit Files'

  const [step, setStep] = useState<typeof STEPS[number]>(initialStep)

  return (
    <Wrapper>
      <Inner withTopPadding flexDirection="column">
        <HeadingRow>
          <H2>Batch Inventory</H2>
          <LinkButton
            minimal
            to={`/election/${electionId}/jurisdiction/${jurisdictionId}`}
            icon="chevron-left"
          >
            Back to Audit Source Data
          </LinkButton>
        </HeadingRow>
        <StepContainer>
          <StepProgress steps={STEPS} currentStep={step} />
          {(() => {
            switch (step) {
              case 'Upload Election Results':
                return (
                  <UploadElectionResultsStep
                    cvrUpload={cvrUpload}
                    tabulatorStatusUpload={tabulatorStatusUpload}
                    nextStep={() => setStep('Inventory Batches')}
                  />
                )
              case 'Inventory Batches':
                return (
                  <InventoryBatchesStep
                    worksheetUrl={`/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/worksheet`}
                    signOffQueries={signOffQueries}
                    prevStep={() => setStep('Upload Election Results')}
                    nextStep={() => setStep('Download Audit Files')}
                  />
                )
              case 'Download Audit Files':
                return (
                  <DownloadAuditFilesStep
                    ballotManifestUrl={`/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/ballot-manifest`}
                    batchTalliesUrl={`/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/batch-tallies`}
                    prevStep={() => setStep('Inventory Batches')}
                  />
                )
              default:
                throw new Error('Unknown step')
            }
          })()}
        </StepContainer>
      </Inner>
    </Wrapper>
  )
}

const BatchInventory: React.FC = () => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()
  const cvrUpload = useBatchInventoryCVR(electionId, jurisdictionId)
  const tabulatorStatusUpload = useBatchInventoryTabulatorStatus(
    electionId,
    jurisdictionId
  )
  const signOffQueries = useBatchInventorySignOff(electionId, jurisdictionId)

  if (
    !(
      cvrUpload.uploadedFile.isSuccess &&
      tabulatorStatusUpload.uploadedFile.isSuccess &&
      signOffQueries.status.isSuccess
    )
  ) {
    return null
  }

  return (
    <BatchInventorySteps
      cvrUpload={cvrUpload}
      tabulatorStatusUpload={tabulatorStatusUpload}
      signOffQueries={signOffQueries}
    />
  )
}

export default BatchInventory
