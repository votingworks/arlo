import React from 'react'
import { toast } from 'react-toastify'
import {
  Button,
  Classes,
  H1,
  H2,
  AnchorButton,
  Intent,
  HTMLSelect,
  Tag,
} from '@blueprintjs/core'
import { useForm } from 'react-hook-form'
import {
  useOrganization,
  useCreateAuditAdmin,
  IAuditAdmin,
  useDeleteOrganization,
  useUpdateOrganization,
  useRemoveAuditAdmin,
  useDeleteElection,
  IElectionBase,
} from './support-api'
import { useConfirm, Confirm } from '../Atoms/Confirm'
import { List, LinkItem } from './List'
import { stateOptions, states } from '../AuditAdmin/Setup/Settings/states'
import { sortBy } from '../../utils/array'
import { AuditStatusTag, Column, Row, Table } from './shared'

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
      toast.success(`Created audit admin: ${auditAdmin.email}`)
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
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        marginTop: '20px',
        width: '100%',
      }}
    >
      <div
        style={{
          display: 'flex',
          gap: '20px',
          alignItems: 'end',
        }}
      >
        <H1 style={{ margin: 0 }}>{name}</H1>
        <div>
          <Button icon="edit" minimal onClick={onClickEditOrg}>
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
      </div>
      <Tag large style={{ alignSelf: 'flex-start' }}>
        {`Default State: ${defaultState ? states[defaultState] : 'None'}`}
      </Tag>
      <Row>
        <Column>
          <H2>Audits</H2>
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
          <H2>Deleted Audits</H2>
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
          <H2>Audit Admins</H2>
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
      </Row>
      <Confirm {...confirmProps} />
    </div>
  )
}

export default Organization
