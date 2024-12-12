import React from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'react-toastify'
import styled from 'styled-components'
import {
  H3,
  Button,
  Classes,
  H2,
  AnchorButton,
  Intent,
  Card,
  MenuItem,
} from '@blueprintjs/core'
import { MultiSelect } from '@blueprintjs/select'
import { useForm, Controller } from 'react-hook-form'
import {
  useJurisdiction,
  useClearAuditBoards,
  useClearOfflineResults,
  useJurisdictionBatches,
  useCreateCombinedBatch,
  useDeleteCombinedBatch,
} from './support-api'
import { useConfirm, Confirm } from '../Atoms/Confirm'
import AuditBoardsTable from '../AuditAdmin/Progress/AuditBoardsTable'
import Breadcrumbs from './Breadcrumbs'
import { Column, Table } from './shared'

const CombinedBatchForm = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1rem;

  label {
    font-weight: 500;
    display: block;
    margin-bottom: 0.25rem;
  }
`

const Jurisdiction = ({ jurisdictionId }: { jurisdictionId: string }) => {
  const jurisdiction = useJurisdiction(jurisdictionId)
  const clearAuditBoards = useClearAuditBoards()
  const clearOfflineResults = useClearOfflineResults()
  const batches = useJurisdictionBatches(jurisdictionId)
  const createCombinedBatch = useCreateCombinedBatch()
  const deleteCombinedBatch = useDeleteCombinedBatch()
  const { confirm, confirmProps } = useConfirm()

  const { register, handleSubmit, reset, control, formState } = useForm<{
    name: string
    subBatchIds: string[]
  }>()

  if (!jurisdiction.isSuccess) return null

  const {
    name,
    organization,
    election,
    jurisdictionAdmins,
    auditBoards,
    recordedResultsAt,
  } = jurisdiction.data

  const onClickClearAuditBoards = () => {
    confirm({
      title: 'Confirm',
      description: `Are you sure you want to clear the audit boards for ${name}?`,
      yesButtonLabel: 'Clear audit boards',
      onYesClick: async () => {
        await clearAuditBoards.mutateAsync({ jurisdictionId })
        toast.success(`Cleared audit boards for ${name}`)
      },
    })
  }

  const onClickClearOfflineResults = () => {
    confirm({
      title: 'Confirm',
      description: `Are you sure you want to clear results for ${name}?`,
      yesButtonLabel: 'Clear results',
      onYesClick: async () => {
        await clearOfflineResults.mutateAsync({
          jurisdictionId,
        })
        toast.success(`Cleared results for ${name}`)
      },
    })
  }

  const onSubmitCreateCombinedBatch = async ({
    // eslint-disable-next-line no-shadow
    name,
    subBatchIds,
  }: {
    name: string
    subBatchIds: string[]
  }) => {
    try {
      await createCombinedBatch.mutateAsync({
        jurisdictionId,
        name,
        subBatchIds,
      })
      reset()
    } catch (error) {
      // Do nothing - errors toasted by queryClient
    }
  }

  return (
    <div style={{ width: '100%' }}>
      <Breadcrumbs>
        <Link to={`/support/orgs/${organization.id}`}>{organization.name}</Link>
        <Link to={`/support/audits/${election.id}`}>{election.auditName}</Link>
      </Breadcrumbs>
      <H2>{name}</H2>
      <div style={{ display: 'flex', width: '100%' }}>
        <Column>
          {election.auditType !== 'BATCH_COMPARISON' && (
            <>
              <H3>Current Round Audit Boards</H3>
              {auditBoards.length === 0 ? (
                <p>The jurisdiction hasn&apos;t created audit boards yet.</p>
              ) : (
                <>
                  <Button
                    intent="danger"
                    onClick={onClickClearAuditBoards}
                    style={{ marginBottom: '10px' }}
                  >
                    Clear audit boards
                  </Button>
                  <AuditBoardsTable auditBoards={auditBoards} />
                </>
              )}
            </>
          )}
          {election.auditType === 'BALLOT_POLLING' && !election.online && (
            <>
              <H3>Offline Results</H3>
              {recordedResultsAt ? (
                <>
                  <p>
                    Results recorded at{' '}
                    {new Date(recordedResultsAt).toLocaleString()}.
                  </p>
                  <Button
                    intent={Intent.DANGER}
                    onClick={onClickClearOfflineResults}
                  >
                    Clear results
                  </Button>
                </>
              ) : (
                <p>No results recorded yet.</p>
              )}
            </>
          )}
          {election.auditType === 'BATCH_COMPARISON' && batches.isSuccess && (
            <>
              <H3>Combined Batches</H3>
              <Card>
                <CombinedBatchForm>
                  <div>
                    <label htmlFor="combinedBatchName">
                      Combined Batch Name:
                    </label>
                    <input
                      type="text"
                      name="name"
                      id="combinedBatchName"
                      className={Classes.INPUT}
                      ref={register}
                      style={{ flexGrow: 1 }}
                      required
                    />
                  </div>
                  <div>
                    <label htmlFor="subBatchIds">Batches to Combine:</label>
                    <Controller
                      name="subBatchIds"
                      control={control}
                      defaultValue={[]}
                      render={({
                        value,
                        onChange,
                      }: {
                        value: string[]
                        onChange: (value: string[]) => void
                      }) => (
                        <MultiSelect
                          items={batches.data.batches}
                          selectedItems={batches.data.batches.filter(batch =>
                            value.includes(batch.id)
                          )}
                          onItemSelect={item => {
                            onChange(
                              value.includes(item.id)
                                ? value.filter(id => id !== item.id)
                                : [...value, item.id]
                            )
                          }}
                          onRemove={item => {
                            onChange(
                              value.filter((id: string) => id !== item.id)
                            )
                          }}
                          itemRenderer={(item, { handleClick, modifiers }) => (
                            <MenuItem
                              key={item.id}
                              text={item.name}
                              onClick={handleClick}
                              active={modifiers.active}
                              icon={value.includes(item.id) ? 'tick' : 'blank'}
                            />
                          )}
                          tagRenderer={item => item.name}
                          itemPredicate={(query, item) =>
                            item.name
                              .toLowerCase()
                              .includes(query.toLowerCase())
                          }
                          placeholder="Select batches..."
                          resetOnSelect
                          fill
                          popoverProps={{ minimal: true }}
                          tagInputProps={{ tagProps: { minimal: true } }}
                        />
                      )}
                    />
                  </div>
                  <Button
                    icon="insert"
                    style={{ alignSelf: 'end' }}
                    loading={formState.isSubmitting}
                    onClick={handleSubmit(onSubmitCreateCombinedBatch)}
                  >
                    Create Combined Batch
                  </Button>
                </CombinedBatchForm>
              </Card>
              {batches.data.combinedBatches.length > 0 && (
                <Table striped>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Batches</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {batches.data.combinedBatches.map(combinedBatch => (
                      <tr key={combinedBatch.name}>
                        <td>{combinedBatch.name}</td>
                        <td style={{ textAlign: 'left' }}>
                          {combinedBatch.subBatches
                            .map(subBatch => subBatch.name)
                            .join(', ')}
                        </td>
                        <td>
                          <Button
                            onClick={() =>
                              deleteCombinedBatch.mutate({
                                jurisdictionId,
                                name: combinedBatch.name,
                              })
                            }
                            loading={deleteCombinedBatch.isLoading}
                            icon="delete"
                            intent="danger"
                            minimal
                          >
                            Delete
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </>
          )}
        </Column>
        <Column>
          <H3>Jurisdiction Admins</H3>
          <Table striped>
            <tbody>
              {jurisdictionAdmins.map(jurisdictionAdmin => (
                <tr key={jurisdictionAdmin.email}>
                  <td>{jurisdictionAdmin.email}</td>
                  <td>
                    <AnchorButton
                      icon="log-in"
                      href={`/api/support/jurisdiction-admins/${jurisdictionAdmin.email}/login`}
                    >
                      Log in as
                    </AnchorButton>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Column>
        <Confirm {...confirmProps} />
      </div>
    </div>
  )
}

export default Jurisdiction
