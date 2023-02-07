import React from 'react'
import { Redirect, Route, Switch } from 'react-router-dom'
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
  ButtonGroup,
  Alignment,
  Colors,
  Intent,
} from '@blueprintjs/core'
import { useForm } from 'react-hook-form'
import { useAuthDataContext } from '../UserContext'
import LinkButton from '../Atoms/LinkButton'
import { Wrapper, Inner } from '../Atoms/Wrapper'
import AsyncButton from '../Atoms/AsyncButton'
import { apiDownload } from '../utilities'
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
} from './support-api'
import { useConfirm, Confirm } from '../Atoms/Confirm'
import AuditBoardsTable from '../AuditAdmin/Progress/AuditBoardsTable'
import RoundsTable from './RoundsTable'

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
              <Organizations />
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

const AuditContainer = styled.div`
  width: 60%;
`

const ButtonList = styled(ButtonGroup).attrs({
  vertical: true,
  minimal: true,
  large: true,
  alignText: Alignment.LEFT,
})`
  margin-bottom: 30px;
  border: 1px solid ${Colors.LIGHT_GRAY3};
  width: 100%;
  .bp3-button {
    border-radius: 0;
    &:not(:first-child) {
      border-top: 1px solid ${Colors.LIGHT_GRAY3};
    }
  }
`

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
      <ButtonList>
        {organizations.data.map(organization => (
          <LinkButton
            key={organization.id}
            to={`/support/orgs/${organization.id}`}
            intent={Intent.PRIMARY}
          >
            {organization.name}
          </LinkButton>
        ))}
      </ButtonList>
    </Column>
  )
}

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
          <ButtonList>
            {elections
              .filter(election => !election.deletedAt)
              .map(election => (
                <LinkButton
                  key={election.id}
                  to={`/support/audits/${election.id}`}
                  intent={Intent.PRIMARY}
                >
                  {election.auditName}
                </LinkButton>
              ))}
          </ButtonList>
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

  const { id, auditName, auditType, jurisdictions, rounds } = election.data

  return (
    <div>
      <H2>{auditName}</H2>
      <AuditContainer>
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
            style={{ marginRight: '10px' }}
            href={`/api/support/elections/${id}/login`}
            icon="log-in"
            intent="primary"
          >
            Log in as audit admin
          </AnchorButton>
          {rounds.length > 0 && (
            <AsyncButton
              intent="primary"
              icon="download"
              onClick={() => apiDownload(`/election/${electionId}/report`)}
            >
              Download Audit Report
            </AsyncButton>
          )}
        </div>
        <div style={{ marginBottom: '10px' }}>
          <RoundsTable electionId={electionId} rounds={rounds} />
        </div>
        <H3>Jurisdictions</H3>
        <ButtonList>
          {jurisdictions.map(jurisdiction => (
            <LinkButton
              key={jurisdiction.id}
              to={`/support/jurisdictions/${jurisdiction.id}`}
              intent={Intent.PRIMARY}
            >
              {jurisdiction.name}
            </LinkButton>
          ))}
        </ButtonList>
      </AuditContainer>
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
