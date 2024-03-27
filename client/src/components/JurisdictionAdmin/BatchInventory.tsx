import React, { useState } from 'react'
import { H2, Button, H4, Checkbox, HTMLSelect } from '@blueprintjs/core'
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
import { CvrFileType, FileProcessingStatus } from '../useCSV'
import {
  IFileUpload,
  useUploadFiles,
  useDeleteFile,
  useUploadedFile,
} from '../useFileUpload'
import { apiDownload, assert } from '../utilities'
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
import { Column, Row } from '../Atoms/Layout'
import {
  BatchInventoryConfig,
  useBatchInventoryFeatureFlag,
} from '../useFeatureFlag'

const STEPS = [
  'Select System',
  'Upload Election Results',
  'Inventory Batches',
  'Download Audit Files',
] as const

const isUploaded = (fileUpload: IFileUpload) =>
  fileUpload.uploadedFile.data?.processing?.status ===
  FileProcessingStatus.PROCESSED

interface ISystemQueries {
  system: UseQueryResult<CvrFileType | null>
  setSystem: UseMutationResult<CvrFileType, unknown, CvrFileType, unknown>
}

const useBatchInventorySystem = (
  electionId: string,
  jurisdictionId: string
): ISystemQueries => {
  const queryClient = useQueryClient()
  const key = ['batchInventory', jurisdictionId, 'system']
  const url = `/api/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/system`
  const system = useQuery<CvrFileType | null>(key, () => fetchApi(url))
  const setSystem = useMutation(
    (systemType: CvrFileType) =>
      fetchApi(url, {
        method: 'PUT',
        body: JSON.stringify({ systemType }),
        headers: { 'Content-Type': 'application/json' },
      }),
    { onSuccess: () => queryClient.invalidateQueries(key) }
  )
  return {
    system,
    setSystem,
  }
}

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
      onFileChange: () => {
        // Tabulator status file is reprocessed when CVR is uploaded
        queryClient.invalidateQueries([
          'batchInventory',
          jurisdictionId,
          'tabulatorStatus',
        ])
        // Sign off is reset if CVR is changed
        queryClient.invalidateQueries([
          'batchInventory',
          jurisdictionId,
          'signOff',
        ])
      },
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
  const queryClient = useQueryClient()
  return {
    uploadedFile: useUploadedFile(key, url, {
      onFileChange: () => {
        // Sign off is reset if tabulator status is changed
        queryClient.invalidateQueries([
          'batchInventory',
          jurisdictionId,
          'signOff',
        ])
      },
    }),
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

const SelectSystemStep: React.FC<{
  systemQueries: ISystemQueries
  nextStep: () => void
}> = ({ systemQueries, nextStep }) => {
  if (!systemQueries.system.isSuccess) {
    return null
  }

  const system = systemQueries.system.data

  const setSystem = async (event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value as CvrFileType
    await systemQueries.setSystem.mutateAsync(value)
  }

  return (
    <>
      <StepPanel>
        <Row alignItems="center" gap="10px" justifyContent="center">
          <span>Select your voting system:</span>
          <HTMLSelect large value={system ?? undefined} onChange={setSystem}>
            {!system && <option value={undefined}></option>}
            <option value={CvrFileType.DOMINION}>Dominion</option>
            <option value={CvrFileType.ESS}>ES&amp;S</option>
          </HTMLSelect>
        </Row>
      </StepPanel>
      <StepActions
        right={
          <Button
            onClick={nextStep}
            intent="primary"
            rightIcon="chevron-right"
            disabled={!system}
          >
            Continue
          </Button>
        }
      />
    </>
  )
}

const UploadElectionResultsStep: React.FC<{
  system: CvrFileType
  cvrUpload: IFileUpload
  tabulatorStatusUpload: IFileUpload
  prevStep: () => void
  nextStep: () => void
}> = ({ system, cvrUpload, tabulatorStatusUpload, prevStep, nextStep }) => {
  return (
    <>
      {system === CvrFileType.DOMINION && (
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
      )}
      {system === CvrFileType.ESS && (
        <StepPanel>
          <StepPanelColumn>
            <FileUpload
              title="Cast Vote Records (CVR)"
              {...cvrUpload}
              acceptFileTypes={['csv', 'zip']}
            />
          </StepPanelColumn>
        </StepPanel>
      )}
      <StepActions
        left={
          <Button icon="chevron-left" onClick={prevStep}>
            Back
          </Button>
        }
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
  showBallotManifest: boolean
  ballotManifestUrl: string
  batchTalliesUrl: string
  prevStep: () => void
}> = ({ showBallotManifest, ballotManifestUrl, batchTalliesUrl, prevStep }) => {
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
          {showBallotManifest ? (
            <p style={{ marginBottom: '15px' }}>
              Next, download the Ballot Manifest and Candidate Totals by Batch
              files, then upload them on the{' '}
              <Link
                to={`/election/${electionId}/jurisdiction/${jurisdictionId}`}
              >
                Audit Setup
              </Link>{' '}
              page.
            </p>
          ) : (
            <p style={{ marginBottom: '15px' }}>
              Next, download this file, then upload it on the{' '}
              <Link
                to={`/election/${electionId}/jurisdiction/${jurisdictionId}`}
              >
                Audit Setup
              </Link>{' '}
              page.
            </p>
          )}
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {showBallotManifest && (
              <AsyncButton
                intent="primary"
                large
                icon="download"
                onClick={() => apiDownload(ballotManifestUrl)}
                style={{ marginBottom: '10px' }}
              >
                Download Ballot Manifest
              </AsyncButton>
            )}
            <AsyncButton
              intent="primary"
              large
              icon="download"
              onClick={() => apiDownload(batchTalliesUrl)}
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
            Return to Audit Setup
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
  batchInventoryConfig: BatchInventoryConfig
  systemQueries: ISystemQueries
  cvrUpload: IFileUpload
  tabulatorStatusUpload: IFileUpload
  signOffQueries: ISignOffQueries
}> = ({
  batchInventoryConfig,
  systemQueries,
  cvrUpload,
  tabulatorStatusUpload,
  signOffQueries,
}) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()

  // Start on the step that's most relevant given progress so far (e.g. if the
  // user left and came back)
  const areFilesUploaded =
    isUploaded(cvrUpload) && isUploaded(tabulatorStatusUpload)
  const isSignedOff = signOffQueries.status.data?.signedOffAt !== null
  const system = systemQueries.system.data
  const initialStep = !system
    ? 'Select System'
    : !areFilesUploaded
    ? 'Upload Election Results'
    : !isSignedOff
    ? 'Inventory Batches'
    : 'Download Audit Files'

  const steps = batchInventoryConfig.generateBallotManifest
    ? STEPS
    : STEPS.filter(step => step !== 'Inventory Batches')

  const [currentStep, setCurrentStep] = useState<typeof STEPS[number]>(
    initialStep
  )
  const currentStepNumber = steps.indexOf(currentStep) + 1

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
            Back to Audit Setup
          </LinkButton>
        </HeadingRow>
        <Steps>
          <StepList>
            {steps.map((step, index) => (
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
              case 'Select System':
                return (
                  <SelectSystemStep
                    systemQueries={systemQueries}
                    nextStep={() => setCurrentStep('Upload Election Results')}
                  />
                )
              case 'Upload Election Results': {
                assert(system !== undefined && system !== null)
                return (
                  <UploadElectionResultsStep
                    system={system}
                    cvrUpload={cvrUpload}
                    tabulatorStatusUpload={tabulatorStatusUpload}
                    prevStep={() => setCurrentStep('Select System')}
                    nextStep={() =>
                      setCurrentStep(
                        batchInventoryConfig.generateBallotManifest
                          ? 'Inventory Batches'
                          : 'Download Audit Files'
                      )
                    }
                  />
                )
              }
              case 'Inventory Batches':
                return (
                  <InventoryBatchesStep
                    worksheetUrl={`/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/worksheet`}
                    signOffQueries={signOffQueries}
                    prevStep={() => setCurrentStep('Upload Election Results')}
                    nextStep={() => setCurrentStep('Download Audit Files')}
                  />
                )
              case 'Download Audit Files': {
                assert(system !== undefined && system !== null)
                return (
                  <DownloadAuditFilesStep
                    showBallotManifest={
                      batchInventoryConfig.generateBallotManifest ||
                      new URLSearchParams(window.location.search).get(
                        'show-ballot-manifest'
                      ) === 'true'
                    }
                    ballotManifestUrl={`/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/ballot-manifest`}
                    batchTalliesUrl={`/election/${electionId}/jurisdiction/${jurisdictionId}/batch-inventory/batch-tallies`}
                    prevStep={() =>
                      setCurrentStep(
                        batchInventoryConfig.generateBallotManifest
                          ? 'Inventory Batches'
                          : 'Upload Election Results'
                      )
                    }
                  />
                )
              }
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
  const systemQueries = useBatchInventorySystem(electionId, jurisdictionId)
  const cvrUpload = useBatchInventoryCVR(electionId, jurisdictionId)
  const tabulatorStatusUpload = useBatchInventoryTabulatorStatus(
    electionId,
    jurisdictionId
  )
  const signOffQueries = useBatchInventorySignOff(electionId, jurisdictionId)
  const batchInventoryConfig = useBatchInventoryFeatureFlag(jurisdictionId)
  assert(batchInventoryConfig !== undefined)

  if (
    !(
      systemQueries.system.isSuccess &&
      cvrUpload.uploadedFile.isSuccess &&
      tabulatorStatusUpload.uploadedFile.isSuccess &&
      signOffQueries.status.isSuccess
    )
  ) {
    return null
  }

  return (
    <BatchInventorySteps
      batchInventoryConfig={batchInventoryConfig}
      systemQueries={systemQueries}
      cvrUpload={cvrUpload}
      tabulatorStatusUpload={tabulatorStatusUpload}
      signOffQueries={signOffQueries}
    />
  )
}

export default BatchInventory
