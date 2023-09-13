import React from 'react'
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
} from '@blueprintjs/core'
import { useForm } from 'react-hook-form'
import { useAuthDataContext } from '../UserContext'
import { Wrapper, Inner } from '../Atoms/Wrapper'
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
  useRenameOrganization,
  useRemoveAuditAdmin,
  useDeleteElection,
  IElectionBase,
  useActiveElections,
} from './support-api'
import { useConfirm, Confirm } from '../Atoms/Confirm'
import AuditBoardsTable from '../AuditAdmin/Progress/AuditBoardsTable'
import RoundsTable from './RoundsTable'
import { List, LinkItem } from './List'
import Breadcrumbs from './Breadcrumbs'

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
      <Inner>
        <div style={{ margin: '30px 0', width: '100%' }}>
          <Switch>
            <Route exact path="/support">
              <Row>
                <ActiveAudits />
                <Organizations />
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
        </div>
      </Inner>
    </Wrapper>
  )
}

const Column = styled.div`
  width: 50%;
  padding-right: 30px;
`

const Row = styled.div`
  display: flex;
  width: 100%;
`

const ActiveAudits = () => {
  const elections = useActiveElections()

  if (!elections.isSuccess) return null

  return (
    <Column>
      <H2>Active Audits</H2>
      <List>
        {elections.data.map(election => (
          <LinkItem key={election.id} to={`/support/audits/${election.id}`}>
            <div>
              <div style={{ color: 'black' }}>{election.organization.name}</div>
              <div className="bp3-text-large">{election.auditName}</div>
            </div>
          </LinkItem>
        ))}
      </List>
    </Column>
  )
}

const Organizations = () => {
  const organizations = useOrganizations()
  const createOrganization = useCreateOrganization()

  const { register, handleSubmit, reset, formState } = useForm<{
    name: string
  }>()

  if (!organizations.isSuccess) return null

  const onSubmitCreateOrganization = async ({ name }: { name: string }) => {
    try {
      await createOrganization.mutateAsync({ name })
      reset()
    } catch (error) {
      // Do nothing - errors toasted by queryClient
    }
  }

  return (
    <Column>
      <H2>Organizations</H2>
      <form
        style={{ display: 'flex', marginBottom: '10px' }}
        onSubmit={handleSubmit(onSubmitCreateOrganization)}
      >
        <input
          type="text"
          name="name"
          className={Classes.INPUT}
          placeholder="New organization name"
          ref={register}
          style={{ flexGrow: 1 }}
        />
        <Button
          type="submit"
          icon="insert"
          style={{ marginLeft: '20px' }}
          loading={formState.isSubmitting}
        >
          Create Organization
        </Button>
      </form>
      <List>
        {organizations.data.map(organization => (
          <LinkItem
            key={organization.id}
            to={`/support/orgs/${organization.id}`}
          >
            {organization.name}
          </LinkItem>
        ))}
      </List>
    </Column>
  )
}

const Organization = ({ organizationId }: { organizationId: string }) => {
  const organization = useOrganization(organizationId)
  const createAuditAdmin = useCreateAuditAdmin(organizationId)
  const removeAuditAdmin = useRemoveAuditAdmin(organizationId)
  const deleteOrganization = useDeleteOrganization(organizationId)
  const renameOrganization = useRenameOrganization(organizationId)
  const deleteElection = useDeleteElection()
  const { confirm, confirmProps } = useConfirm()

  const {
    register: registerCreateAdmin,
    handleSubmit: handleSubmitCreateAdmin,
    reset: resetCreateAdmin,
    formState: formStateCreateAdmin,
  } = useForm<IAuditAdmin>()
  const {
    register: registerRename,
    handleSubmit: handleSubmitRename,
  } = useForm<{ name: string }>()

  if (!organization.isSuccess) return null

  const onSubmitCreateAuditAdmin = async (auditAdmin: IAuditAdmin) => {
    try {
      await createAuditAdmin.mutateAsync(auditAdmin)
      resetCreateAdmin()
    } catch (error) {
      // Do nothing - errors toasted by queryClient
    }
  }

  const { name, elections, auditAdmins } = organization.data

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

  const onClickRenameOrg = () =>
    confirm({
      title: 'Rename',
      description: (
        <form>
          <label htmlFor="name">
            <p>Enter a new name for this organization: </p>
            <input
              type="text"
              name="name"
              id="name"
              className={Classes.INPUT}
              ref={registerRename}
              style={{ width: '100%' }}
            />
          </label>
        </form>
      ),
      yesButtonLabel: 'Submit',
      // eslint-disable-next-line no-shadow
      onYesClick: handleSubmitRename(async ({ name }: { name: string }) => {
        await renameOrganization.mutateAsync({ name })
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
          onClick={onClickRenameOrg}
          style={{ marginLeft: '10px' }}
        >
          Rename
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

      <div style={{ display: 'flex', width: '100%' }}>
        <Column>
          <H3>Audits</H3>
          <List style={{ marginBottom: '30px' }}>
            {elections
              .filter(election => !election.deletedAt)
              .map(election => (
                <LinkItem
                  key={election.id}
                  to={`/support/audits/${election.id}`}
                >
                  {election.auditName}
                </LinkItem>
              ))}
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
    <div>
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

const Jurisdiction = ({ jurisdictionId }: { jurisdictionId: string }) => {
  const jurisdiction = useJurisdiction(jurisdictionId)
  const clearAuditBoards = useClearAuditBoards()
  const clearOfflineResults = useClearOfflineResults()
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
