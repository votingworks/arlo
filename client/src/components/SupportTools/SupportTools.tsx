import React, { useState } from 'react'
import { Redirect, Route, Switch } from 'react-router-dom'
import { toast } from 'react-toastify'
import styled from 'styled-components'
import { Button, Classes, AnchorButton, Tooltip, H1 } from '@blueprintjs/core'
import { useForm } from 'react-hook-form'
import { useAuthDataContext } from '../UserContext'
import { Wrapper, SupportToolsInner } from '../Atoms/Wrapper'
import {
  useOrganizations,
  useCreateOrganization,
  useActiveElections,
} from './support-api'
import { List, LinkItem } from './List'
import Audit from './Audit'
import Organization from './Organization'
import Jurisdiction from './Jurisdiction'
import { AuditStatusTag, Row } from './shared'
import { FilterInput } from '../Atoms/Table'
import H2Title from '../Atoms/H2Title'

const SupportTools: React.FC = () => {
  const auth = useAuthDataContext()
  if (!auth) return null // Still loading
  if (!auth.supportUser) return <Redirect to="/" />

  return (
    <Wrapper>
      <SupportToolsInner>
        <Switch>
          <Route exact path="/support">
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                width: '100%',
              }}
            >
              <Row>
                <H1>Support Tools</H1>
              </Row>
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
            </div>
          </Route>
          <Route path="/support/orgs/:organizationId">
            {({ match }: any) => (
              <Organization organizationId={match!.params.organizationId} />
            )}
          </Route>
          <Route path="/support/audits/:electionId">
            {({ match }: any) => (
              <Audit electionId={match!.params.electionId} />
            )}
          </Route>
          <Route path="/support/jurisdictions/:jurisdictionId">
            {({ match }: any) => (
              <Jurisdiction jurisdictionId={match!.params.jurisdictionId} />
            )}
          </Route>
        </Switch>
      </SupportToolsInner>
    </Wrapper>
  )
}

const ActiveAudits = () => {
  const elections = useActiveElections()

  if (!elections.isSuccess) return null

  return (
    <>
      <H2Title>Active Audits</H2Title>
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
      <H2Title>Organizations</H2Title>
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
      <H2Title>Tools</H2Title>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
        }}
      >
        <form
          style={{ display: 'flex', gap: '8px' }}
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

export default SupportTools
