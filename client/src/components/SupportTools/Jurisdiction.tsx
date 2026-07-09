import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'react-toastify'
import styled from 'styled-components'
import {
  H1,
  Button,
  Classes,
  AnchorButton,
  Intent,
  Card,
  MenuItem,
  Menu,
} from '@blueprintjs/core'
import { MultiSelect, renderFilteredItems } from '@blueprintjs/select'
import { useForm, Controller } from 'react-hook-form'
import {
  IBatch,
  ICombinedBatch,
  useJurisdiction,
  useClearAuditBoards,
  useClearOfflineResults,
  useJurisdictionBatches,
  useCreateCombinedBatch,
  useDeleteCombinedBatch,
  useSetRequiredBatches,
} from './support-api'
import { useConfirm, Confirm } from '../Atoms/Confirm'
import AuditBoardsTable from '../AuditAdmin/Progress/AuditBoardsTable'
import Breadcrumbs from './Breadcrumbs'
import { Column, Row, Table } from './shared'
import H2Title from '../Atoms/H2Title'

const BatchForm = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1rem;

  label {
    font-weight: 500;
    display: block;
    margin-bottom: 0.25rem;
  }
`

const BatchMultiSelect = ({
  batches,
  selectedBatchIds,
  onChange,
  placeholder = 'Search by batch name...',
}: {
  batches: IBatch[]
  selectedBatchIds: string[]
  onChange: (batchIds: string[]) => void
  placeholder?: string
}) => (
  <MultiSelect
    items={batches}
    selectedItems={batches.filter(batch => selectedBatchIds.includes(batch.id))}
    onItemSelect={item => {
      onChange(
        selectedBatchIds.includes(item.id)
          ? selectedBatchIds.filter(id => id !== item.id)
          : [...selectedBatchIds, item.id]
      )
    }}
    onRemove={item => {
      onChange(selectedBatchIds.filter((id: string) => id !== item.id))
    }}
    itemListRenderer={itemListProps => (
      <Menu
        ulRef={
          itemListProps.itemsParentRef as (ref: HTMLUListElement | null) => void
        }
        style={{ maxHeight: 350, overflowY: 'auto' }}
      >
        {renderFilteredItems(
          itemListProps,
          <MenuItem disabled text="No matching batches." />
        )}
      </Menu>
    )}
    itemRenderer={(item, { handleClick, modifiers }) => (
      <MenuItem
        key={item.id}
        text={item.name}
        onClick={handleClick}
        active={modifiers.active}
        icon={selectedBatchIds.includes(item.id) ? 'tick' : 'blank'}
      />
    )}
    tagRenderer={item => item.name}
    itemPredicate={(query, item) =>
      item.name.toLowerCase().includes(query.toLowerCase())
    }
    placeholder={placeholder}
    resetOnSelect
    fill
    popoverProps={{ minimal: true }}
    tagInputProps={{ tagProps: { minimal: true } }}
  />
)

const RequiredBatchesForm = ({
  jurisdictionId,
  batches,
}: {
  jurisdictionId: string
  batches: IBatch[]
}) => {
  const setRequiredBatches = useSetRequiredBatches()
  const [requiredBatchIds, setRequiredBatchIds] = useState(() =>
    batches.filter(batch => batch.required).map(batch => batch.id)
  )

  const onClickSave = async () => {
    try {
      await setRequiredBatches.mutateAsync({
        jurisdictionId,
        batchIds: requiredBatchIds,
      })
      toast.success('Saved required batches')
    } catch (error) {
      // Do nothing - errors toasted by queryClient
    }
  }

  return (
    <Card>
      <BatchForm>
        <div>
          <label htmlFor="requiredBatchIds">Batches to Require:</label>
          <BatchMultiSelect
            batches={batches}
            selectedBatchIds={requiredBatchIds}
            onChange={setRequiredBatchIds}
            placeholder="Search by batch name to require..."
          />
        </div>
        <Button
          icon="tick"
          style={{ alignSelf: 'end' }}
          loading={setRequiredBatches.isLoading}
          onClick={onClickSave}
        >
          Save Required Batches
        </Button>
      </BatchForm>
    </Card>
  )
}

const CombinedBatchesForm = ({
  jurisdictionId,
  batches,
  combinedBatches,
}: {
  jurisdictionId: string
  batches: IBatch[]
  combinedBatches: ICombinedBatch[]
}) => {
  const createCombinedBatch = useCreateCombinedBatch()
  const deleteCombinedBatch = useDeleteCombinedBatch()

  const { register, handleSubmit, reset, control, formState } = useForm<{
    name: string
    subBatchIds: string[]
  }>()

  const onSubmitCreateCombinedBatch = async ({
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
    <>
      <Card>
        <BatchForm>
          <div>
            <label htmlFor="combinedBatchName">Combined Batch Name:</label>
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
                value: string[] // eslint-disable-line react/no-unused-prop-types
                onChange: (value: string[]) => void // eslint-disable-line react/no-unused-prop-types
              }) => (
                <BatchMultiSelect
                  batches={batches}
                  selectedBatchIds={value}
                  onChange={onChange}
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
        </BatchForm>
      </Card>
      {combinedBatches.length > 0 && (
        <Table striped>
          <thead>
            <tr>
              <th>Name</th>
              <th>Batches</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {combinedBatches.map(combinedBatch => (
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
  )
}

const Jurisdiction = ({ jurisdictionId }: { jurisdictionId: string }) => {
  const jurisdiction = useJurisdiction(jurisdictionId)
  const clearAuditBoards = useClearAuditBoards()
  const clearOfflineResults = useClearOfflineResults()
  const batches = useJurisdictionBatches(jurisdictionId)
  const { confirm, confirmProps } = useConfirm()

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

  return (
    <div
      style={{
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        marginTop: '20px',
      }}
    >
      <Breadcrumbs>
        <Link to={`/support/orgs/${organization.id}`}>{organization.name}</Link>
        <Link to={`/support/audits/${election.id}`}>{election.auditName}</Link>
      </Breadcrumbs>
      <H1>{name}</H1>
      <Row>
        <Column>
          {election.auditType !== 'BATCH_COMPARISON' && (
            <>
              <H2Title>Current Round Audit Boards</H2Title>
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
              <H2Title>Offline Results</H2Title>
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
              <H2Title>Required Batches</H2Title>
              <RequiredBatchesForm
                key={`required-batches-${jurisdictionId}`}
                jurisdictionId={jurisdictionId}
                batches={batches.data.batches}
              />
              <H2Title>Combined Batches</H2Title>
              <CombinedBatchesForm
                key={`combined-batches-${jurisdictionId}`}
                jurisdictionId={jurisdictionId}
                batches={batches.data.batches}
                combinedBatches={batches.data.combinedBatches}
              />
            </>
          )}
        </Column>
        <Column>
          <H2Title>Jurisdiction Admins</H2Title>
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
      </Row>
    </div>
  )
}

export default Jurisdiction
