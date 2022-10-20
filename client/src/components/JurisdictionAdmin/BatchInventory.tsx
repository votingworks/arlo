import React, { useState } from 'react'
import { H2, Button, H4, Checkbox } from '@blueprintjs/core'
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
import {
  StepPanel,
  StepActions,
  Steps,
  StepList,
  StepListItem,
  stepState,
  StepPanelColumn,
} from '../Atoms/Steps'
import { Column } from '../Atoms/Layout'

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

const UploadElectionResultsStep: React.FC<{
  nextStep: () => void
  cvrUpload: IFileUpload
  tabulatorStatusUpload: IFileUpload
}> = ({ nextStep, cvrUpload, tabulatorStatusUpload }) => {
  return (
    <>
      <StepPanel>
        <StepPanelColumn>
          <FileUpload
            title="Cast Vote Records (CVR)"
            {...cvrUpload}
            acceptFileTypes={['csv']}
          />
        </StepPanelColumn>
        <StepPanelColumn>
          <FileUpload
            title="Tabulator Status"
            {...tabulatorStatusUpload}
            acceptFileTypes={['xml']}
            uploadDisabled={!isUploaded(cvrUpload)}
          />
        </StepPanelColumn>
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
        <Column justifyContent="center" alignItems="center">
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
        </Column>
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
        <Column
          justifyContent="center"
          alignItems="center"
          style={{ maxWidth: '50%' }}
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
        </Column>
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

  const [currentStep, setCurrentStep] = useState<typeof STEPS[number]>(
    initialStep
  )
  const currentStepNumber = STEPS.indexOf(currentStep) + 1

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
        <Steps>
          <StepList>
            {STEPS.map((step, index) => (
              <StepListItem
                key={step}
                stepNumber={index + 1}
                state={stepState(index + 1, currentStepNumber)}
              >
                {step}
              </StepListItem>
            ))}
          </StepList>
          {(() => {
            switch (currentStep) {
              case 'Upload Election Results':
                return (
                  <UploadElectionResultsStep
                    cvrUpload={cvrUpload}
                    tabulatorStatusUpload={tabulatorStatusUpload}
                    nextStep={() => setCurrentStep('Inventory Batches')}
                  />
                )
              case 'Inventory Batches':
                return (
                  <InventoryBatchesStep
                    worksheetUrl={`/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/worksheet`}
                    signOffQueries={signOffQueries}
                    prevStep={() => setCurrentStep('Upload Election Results')}
                    nextStep={() => setCurrentStep('Download Audit Files')}
                  />
                )
              case 'Download Audit Files':
                return (
                  <DownloadAuditFilesStep
                    ballotManifestUrl={`/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/ballot-manifest`}
                    batchTalliesUrl={`/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/batch-tallies`}
                    prevStep={() => setCurrentStep('Inventory Batches')}
                  />
                )
              default:
                throw new Error('Unknown step')
            }
          })()}
        </Steps>
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
