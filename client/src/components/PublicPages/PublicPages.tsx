import React from 'react'
import { Redirect, Route, Switch } from 'react-router-dom'

import AuditPlanner from './AuditPlanner'
import { Wrapper } from '../Atoms/Wrapper'

const PublicPages: React.FC = () => {
  return (
    <Wrapper>
      <Switch>
        <Route exact path="/public/audit-planner">
          <AuditPlanner />
        </Route>
        <Route>
          <Redirect to="/" />
        </Route>
      </Switch>
    </Wrapper>
  )
}

export default PublicPages
