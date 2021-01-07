import React from 'react'
import { ReactQueryDevtools } from 'react-query/devtools'
import { QueryClientProvider, QueryClient } from 'react-query'
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
  H4,
} from '@blueprintjs/core'
import { useForm } from 'react-hook-form'
import { useAuthDataContext } from '../UserContext'
import LinkButton from '../Atoms/LinkButton'
import { Wrapper, Inner } from '../Atoms/Wrapper'
import {
  useOrganizations,
  useOrganization,
  useCreateAuditAdmin,
  useElection,
  IAuditAdmin,
  IElection,
} from './support-api'

const queryClient = new QueryClient()

const SupportTools = () => {
  const auth = useAuthDataContext()
  if (!auth) return null // Still loading
  if (!auth.superadminUser) return <Redirect to="/" />

  return (
    <QueryClientProvider client={queryClient}>
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
            </Switch>
          </div>
        </Inner>
      </Wrapper>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}

const UL = styled.ul`
  padding: 0;
  list-style-type: none;
  li {
    padding: 5px 0;
    > .bp3-button:first-child {
      margin-left: -10px;
    }
  }
`

const Organizations = () => {
  const organizations = useOrganizations()
  if (organizations.isLoading || organizations.isIdle) return null
  if (organizations.isError) {
    toast.error(organizations.error.message)
    return null
  }

  return (
    <div>
      <H2>Organizations</H2>
      <UL>
        {organizations.data.map(organization => (
          <li key={organization.id}>
            <LinkButton to={`/support/orgs/${organization.id}`} minimal>
              {organization.name}
            </LinkButton>
          </li>
        ))}
      </UL>
    </div>
  )
}

const Table = styled(HTMLTable)`
  margin-top: 10px;
  width: 380px;
  table-layout: fixed;
  td:first-child {
    width: 230px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  tr td {
    vertical-align: baseline;
  }
`

const Organization = ({ organizationId }: { organizationId: string }) => {
  const organization = useOrganization(organizationId)
  const createAuditAdmin = useCreateAuditAdmin()

  const { register, handleSubmit, reset, formState } = useForm<IAuditAdmin>()

  if (organization.isLoading || organization.isIdle) return null
  if (organization.isError) {
    toast.error(organization.error.message)
    return null
  }

  const onSubmitCreateAuditAdmin = async (auditAdmin: IAuditAdmin) => {
    try {
      await createAuditAdmin.mutateAsync({ organizationId, auditAdmin })
      reset()
    } catch (error) {
      toast.error(error.message)
    }
  }

  const { name, elections, auditAdmins } = organization.data

  return (
    <div style={{ width: '100%' }}>
      <H2>{name}</H2>
      <div style={{ display: 'flex', width: '100%' }}>
        <div style={{ width: '50%' }}>
          <H3>Audits</H3>
          <UL>
            {elections.map(election => (
              <li key={election.id}>
                <LinkButton to={`/support/audits/${election.id}`} minimal>
                  {election.auditName}
                </LinkButton>
              </li>
            ))}
          </UL>
        </div>
        <div style={{ width: '50%' }}>
          <H3>Audit Admins</H3>
          <form onSubmit={handleSubmit(onSubmitCreateAuditAdmin)}>
            <input
              type="text"
              name="email"
              className={Classes.INPUT}
              placeholder="New admin email"
              ref={register}
            />
            <Button
              type="submit"
              icon="new-person"
              style={{ marginLeft: '20px' }}
              loading={formState.isSubmitting}
            >
              Create Audit Admin
            </Button>
          </form>
          <Table striped>
            <tbody>
              {auditAdmins.map(auditAdmin => (
                <tr key={auditAdmin.email}>
                  <td>{auditAdmin.email}</td>
                  <td>
                    <AnchorButton
                      icon="log-in"
                      style={{ marginLeft: '20px' }}
                      href={`/api/support/audit-admins/${auditAdmin.email}/login`}
                    >
                      Log in as
                    </AnchorButton>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      </div>
    </div>
  )
}

const prettyAuditType = (auditType: IElection['auditType']) =>
  ({
    BALLOT_POLLING: 'Ballot Polling',
    BALLOT_COMPARISON: 'Ballot Comparison',
    BATCH_COMPARISON: 'Batch Comparison',
  }[auditType])

const Audit = ({ electionId }: { electionId: string }) => {
  const election = useElection(electionId)

  if (election.isLoading || election.isIdle) return null
  if (election.isError) {
    toast.error(election.error.message)
    return null
  }

  const { auditName, auditType, jurisdictions } = election.data

  return (
    <div>
      <H2>{auditName}</H2>
      <Tag large style={{ marginBottom: '15px' }}>
        {prettyAuditType(auditType)}
      </Tag>
      <H3>Jurisdictions</H3>
      {jurisdictions.map(jurisdiction => (
        <div key={jurisdiction.id} style={{ marginTop: '15px' }}>
          <H4>{jurisdiction.name}</H4>
          <Table striped>
            <tbody>
              {jurisdiction.jurisdictionAdmins.map(jurisdictionAdmin => (
                <tr key={jurisdictionAdmin.email}>
                  <td>{jurisdictionAdmin.email}</td>
                  <td>
                    <AnchorButton
                      icon="log-in"
                      style={{ marginLeft: '20px' }}
                      href={`/api/support/jurisdiction-admins/${jurisdictionAdmin.email}/login`}
                    >
                      Log in as
                    </AnchorButton>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      ))}
    </div>
  )
}

export default SupportTools
