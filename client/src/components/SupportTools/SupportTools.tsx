import React, { useState } from 'react'
import { Redirect, Route, Switch, Link } from 'react-router-dom'
import { toast } from 'react-toastify'
import styled from 'styled-components'
import {
  H3,
  Button,
  HTMLTable,
  Classes,
  H2,
  AnchorButton,
  Tag,
  Intent,
  HTMLSelect,
  Card,
  MenuItem,
  Tooltip,
} from '@blueprintjs/core'
import { MultiSelect } from '@blueprintjs/select'
import { useForm, Controller } from 'react-hook-form'
import { useAuthDataContext } from '../UserContext'
import { Wrapper, SupportToolsInner } from '../Atoms/Wrapper'
import {
  useOrganizations,
  useOrganization,
  useCreateAuditAdmin,
  useElection,
  IAuditAdmin,
  IElection,
  useCreateOrganization,
  useJurisdiction,
  useClearAuditBoards,
  useClearOfflineResults,
  useDeleteOrganization,
  useUpdateOrganization,
  useRemoveAuditAdmin,
  useDeleteElection,
  IElectionBase,
  useActiveElections,
  useJurisdictionBatches,
  useCreateCombinedBatch,
  useDeleteCombinedBatch,
  IRound,
} from './support-api'
import { useConfirm, Confirm } from '../Atoms/Confirm'
import AuditBoardsTable from '../AuditAdmin/Progress/AuditBoardsTable'
import RoundsTable from './RoundsTable'
import { List, LinkItem } from './List'
import Breadcrumbs from './Breadcrumbs'
import { stateOptions, states } from '../AuditAdmin/Setup/Settings/states'
import StatusTag from '../Atoms/StatusTag'
import { sortBy } from '../../utils/array'
import { FilterInput } from '../Atoms/Table'

const Table = styled(HTMLTable)`
  margin: 10px 0;
  width: 100%;
  table-layout: fixed;
  td:first-child {
    overflow: hidden;
    text-overflow: ellipsis;
  }
  td:last-child:not(:first-child) {
    padding-right: 15px;
    text-align: right;
  }
  tr td {
    vertical-align: baseline;
  }
`

const SupportTools: React.FC = () => {
  const auth = useAuthDataContext()
  if (!auth) return null // Still loading
  if (!auth.supportUser) return <Redirect to="/" />

  return (
    <Wrapper>
      <SupportToolsInner>
        <Switch>
          <Route exact path="/support">
            <Row>
              <div style={{ flex: '0 0 25%' }}>
                <Organizations />
              </div>
              <div style={{ flex: '0 1 50%' }}>
                <ActiveAudits />
              </div>
              <div style={{ flex: '0 0 25%' }}>
                <Tools />
              </div>
            </Row>
          </Route>
          <Route path="/support/orgs/:organizationId">
            {({ match }) => (
              <Organization organizationId={match!.params.organizationId} />
            )}
          </Route>
          <Route path="/support/audits/:electionId">
            {({ match }) => <Audit electionId={match!.params.electionId} />}
          </Route>
          <Route path="/support/jurisdictions/:jurisdictionId">
            {({ match }) => (
              <Jurisdiction jurisdictionId={match!.params.jurisdictionId} />
            )}
          </Route>
        </Switch>
      </SupportToolsInner>
    </Wrapper>
  )
}

const Column = styled.div`
  width: 50%;
  padding-right: 30px;
`

const Row = styled.div`
  display: flex;
  gap: 30px;
  width: 100%;
`

const AuditStatusTag = ({ currentRound }: { currentRound: IRound | null }) => {
  if (!currentRound) {
    return <StatusTag>Not Started</StatusTag>
  }
  if (currentRound.endedAt) {
    return <StatusTag intent="success">Completed</StatusTag>
  }
  return (
    <StatusTag intent="warning">
      Round {currentRound.roundNum} In Progress
    </StatusTag>
  )
}

const ActiveAudits = () => {
  const elections = useActiveElections()

  if (!elections.isSuccess) return null

  return (
    <>
      <H3 style={{ marginBottom: '20px' }}>Active Audits</H3>
      <List>
        {elections.data.map(election => (
          <LinkItem key={election.id} to={`/support/audits/${election.id}`}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                width: '100%',
              }}
            >
              <div>
                <div style={{ color: 'black' }}>
                  {election.organization.name}
                </div>
                <div className="bp3-text-large">{election.auditName}</div>
              </div>
              <AuditStatusTag currentRound={election.currentRound} />
            </div>
          </LinkItem>
        ))}
      </List>
    </>
  )
}

const Organizations = () => {
  const organizations = useOrganizations()
  const [filterText, setFilterText] = useState<string>('')

  if (!organizations.isSuccess) return null

  return (
    <>
      <H3 style={{ marginBottom: '20px' }}>Organizations</H3>
      <FilterInput
        onChange={setFilterText}
        placeholder="Filter organizations..."
        value={filterText}
      />
      <List style={{ marginTop: '20px' }}>
        {organizations.data
          .filter(org =>
            org.name
              .toLocaleLowerCase()
              .includes(filterText.toLocaleLowerCase())
          )
          .map(organization => (
            <LinkItem
              key={organization.id}
              to={`/support/orgs/${organization.id}`}
            >
              {organization.name}
            </LinkItem>
          ))}
      </List>
    </>
  )
}

const DownloadUsersButton = styled(AnchorButton)`
  margin-bottom: 10px;
`

const Tools = () => {
  const createOrganization = useCreateOrganization()

  const { register, handleSubmit, reset, formState } = useForm<{
    name: string
  }>()

  const onSubmitCreateOrganization = async ({ name }: { name: string }) => {
    try {
      await createOrganization.mutateAsync({ name })
      toast.success(
        `Created organization for '${name}'. You will find it in the Organizations list.`
      )
      reset()
    } catch (error) {
      // Do nothing - errors toasted by queryClient
    }
  }

  return (
    <>
      <H3 style={{ marginBottom: '20px' }}>Tools</H3>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
        }}
      >
        <form
          style={{
            display: 'flex',
            gap: '8px',
          }}
          onSubmit={handleSubmit(onSubmitCreateOrganization)}
        >
          <Button
            type="submit"
            icon="insert"
            loading={formState.isSubmitting}
            disabled={!formState.isDirty}
            style={{ flexShrink: 0 }}
          >
            Create Org
          </Button>
          <input
            type="text"
            name="name"
            className={Classes.INPUT}
            placeholder="Organization name"
            ref={register}
            style={{ width: '100%' }}
          />
        </form>
        <div>
          <Tooltip
            content={
              <p>
                Export a list of Audit Admins and Jurisdiction Managers for all
                audits completed in the last 12 weeks.
              </p>
            }
          >
            <DownloadUsersButton
              icon="download"
              intent="none"
              href="/api/support/organizations/users"
            >
              Download User List
            </DownloadUsersButton>
          </Tooltip>
        </div>
      </div>
    </>
  )
}

const Organization = ({ organizationId }: { organizationId: string }) => {
  const organization = useOrganization(organizationId)
  const createAuditAdmin = useCreateAuditAdmin(organizationId)
  const removeAuditAdmin = useRemoveAuditAdmin(organizationId)
  const deleteOrganization = useDeleteOrganization(organizationId)
  const updateOrganization = useUpdateOrganization(organizationId)
  const deleteElection = useDeleteElection()
  const { confirm, confirmProps } = useConfirm()

  const {
    register: registerCreateAdmin,
    handleSubmit: handleSubmitCreateAdmin,
    reset: resetCreateAdmin,
    formState: formStateCreateAdmin,
  } = useForm<IAuditAdmin>()
  const {
    register: registerEditOrg,
    handleSubmit: handleSubmitEditOrg,
  } = useForm<{ name: string; defaultState?: string | null }>()

  if (!organization.isSuccess) return null

  const onSubmitCreateAuditAdmin = async (auditAdmin: IAuditAdmin) => {
    try {
      await createAuditAdmin.mutateAsync(auditAdmin)
      resetCreateAdmin()
    } catch (error) {
      // Do nothing - errors toasted by queryClient
    }
  }

  const { name, defaultState, elections, auditAdmins } = organization.data

  const sortedElections = sortBy(elections, a =>
    new Date(a.createdAt).getTime()
  ).reverse()

  const onClickRemoveAuditAdmin = (auditAdmin: IAuditAdmin) =>
    confirm({
      title: 'Confirm',
      description: `Are you sure you want to remove audit admin ${auditAdmin.email} from organization ${name}?`,
      yesButtonLabel: 'Remove',
      onYesClick: async () => {
        await removeAuditAdmin.mutateAsync({ auditAdminId: auditAdmin.id })
        toast.success(`Removed audit admin ${auditAdmin.email}`)
      },
    })

  const onClickDeleteOrg = () =>
    confirm({
      title: 'Confirm',
      description: `Are you sure you want to delete organization ${name}?`,
      yesButtonLabel: 'Delete',
      onYesClick: async () => {
        await deleteOrganization.mutateAsync()
        toast.success(`Deleted organization ${name}`)
      },
    })

  const onClickEditOrg = () =>
    confirm({
      title: 'Edit Organization',
      description: (
        <form>
          <label
            htmlFor="name"
            style={{ display: 'block', marginBottom: '3px' }}
          >
            Name:
          </label>
          <input
            type="text"
            name="name"
            id="name"
            className={Classes.INPUT}
            defaultValue={name}
            ref={registerEditOrg}
            style={{ width: '100%', marginBottom: '15px' }}
          />
          <label
            htmlFor="defaultState"
            style={{ display: 'block', marginBottom: '3px' }}
          >
            Default State:
          </label>
          <HTMLSelect
            name="defaultState"
            id="defaultState"
            defaultValue={defaultState || undefined}
            elementRef={registerEditOrg}
          >
            <option value=""></option>
            {stateOptions.map(({ value, label }) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </HTMLSelect>
        </form>
      ),
      yesButtonLabel: 'Submit',
      onYesClick: handleSubmitEditOrg(async values => {
        await updateOrganization.mutateAsync({
          name: values.name,
          defaultState: values.defaultState || null,
        })
      }),
    })

  const onClickPermanentlyDeleteAudit = ({ auditName, id }: IElectionBase) => {
    confirm({
      title: 'Confirm',
      description: `Are you sure you want to permanently delete ${auditName}?`,
      yesButtonLabel: 'Delete',
      onYesClick: async () => {
        await deleteElection.mutateAsync({ electionId: id, organizationId })
        toast.success(`Deleted ${auditName}`)
      },
    })
  }

  return (
    <div style={{ width: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'baseline' }}>
        <H2>{name}</H2>
        <Button
          icon="edit"
          minimal
          onClick={onClickEditOrg}
          style={{ marginLeft: '10px' }}
        >
          Edit
        </Button>
        <Button
          icon="delete"
          intent={Intent.DANGER}
          minimal
          onClick={onClickDeleteOrg}
        >
          Delete
        </Button>
      </div>
      <p>Default State: {defaultState ? states[defaultState] : 'None'}</p>
      <div style={{ display: 'flex', width: '100%' }}>
        <Column>
          <H3>Audits</H3>
          <List style={{ marginBottom: '30px' }}>
            {sortedElections
              .filter(election => !election.deletedAt)
              .map(election => {
                return (
                  <LinkItem
                    key={election.id}
                    to={`/support/audits/${election.id}`}
                  >
                    {election.auditName}
                    <AuditStatusTag currentRound={election.currentRound} />
                  </LinkItem>
                )
              })}
          </List>
          <H3>Deleted Audits</H3>
          <Table striped>
            <tbody>
              {elections
                .filter(election => election.deletedAt)
                .map(election => (
                  <tr key={election.id}>
                    <td>{election.auditName}</td>
                    <td>
                      <Button
                        icon="delete"
                        intent={Intent.DANGER}
                        onClick={() => onClickPermanentlyDeleteAudit(election)}
                        minimal
                      >
                        Permanently Delete
                      </Button>
                    </td>
                  </tr>
                ))}
            </tbody>
          </Table>
        </Column>
        <Column>
          <H3>Audit Admins</H3>
          <form
            style={{ display: 'flex' }}
            onSubmit={handleSubmitCreateAdmin(onSubmitCreateAuditAdmin)}
          >
            <input
              type="text"
              name="email"
              className={Classes.INPUT}
              placeholder="New admin email"
              ref={registerCreateAdmin}
              style={{ flexGrow: 1 }}
            />
            <Button
              type="submit"
              icon="new-person"
              style={{ marginLeft: '20px' }}
              loading={formStateCreateAdmin.isSubmitting}
              intent="primary"
            >
              Create Audit Admin
            </Button>
          </form>
          <Table striped style={{ tableLayout: 'auto' }}>
            <tbody>
              {auditAdmins.map(auditAdmin => (
                <tr key={auditAdmin.email}>
                  <td>{auditAdmin.email}</td>
                  <td>
                    <AnchorButton
                      icon="log-in"
                      href={`/api/support/audit-admins/${auditAdmin.email}/login`}
                      style={{ marginRight: '5px' }}
                    >
                      Log in as
                    </AnchorButton>
                    <Button
                      icon="delete"
                      onClick={() => onClickRemoveAuditAdmin(auditAdmin)}
                      minimal
                      intent="danger"
                    >
                      Remove
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Column>
      </div>
      <Confirm {...confirmProps} />
    </div>
  )
}

const prettyAuditType = (auditType: IElection['auditType']) =>
  ({
    BALLOT_POLLING: 'Ballot Polling',
    BALLOT_COMPARISON: 'Ballot Comparison',
    BATCH_COMPARISON: 'Batch Comparison',
    HYBRID: 'Hybrid',
  }[auditType])

const Audit = ({ electionId }: { electionId: string }) => {
  const election = useElection(electionId)

  if (!election.isSuccess) return null

  const {
    id,
    auditName,
    auditType,
    organization,
    jurisdictions,
    rounds,
  } = election.data

  return (
    <div style={{ width: '100%' }}>
      <Breadcrumbs>
        <Link to={`/support/orgs/${organization.id}`}>{organization.name}</Link>
      </Breadcrumbs>
      <H2>{auditName}</H2>
      <Column>
        <div
          style={{
            alignItems: 'center',
            display: 'flex',
            marginBottom: '10px',
          }}
        >
          <Tag large style={{ marginRight: '10px' }}>
            {prettyAuditType(auditType)}
          </Tag>
          <AnchorButton
            href={`/api/support/elections/${id}/login`}
            icon="log-in"
            intent="primary"
          >
            Log in as audit admin
          </AnchorButton>
        </div>
        <div style={{ marginBottom: '10px' }}>
          <RoundsTable electionId={electionId} rounds={rounds} />
        </div>
        <H3>Jurisdictions</H3>
        <List>
          {jurisdictions.map(jurisdiction => (
            <LinkItem
              to={`/support/jurisdictions/${jurisdiction.id}`}
              key={jurisdiction.id}
            >
              {jurisdiction.name}
              <AnchorButton
                href={`/api/support/jurisdictions/${jurisdiction.id}/login`}
                icon="log-in"
                onClick={(e: React.MouseEvent) => e.stopPropagation()}
              >
                Log in
              </AnchorButton>
            </LinkItem>
          ))}
        </List>
      </Column>
    </div>
  )
}

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

export default SupportTools
