import React from 'react'
import { Route, Switch } from 'react-router-dom'

import AuditPlanner from './AuditPlanner'
import NotFound from './NotFound'
import { Wrapper } from '../Atoms/Wrapper'

const PublicPages: React.FC = () => {
  return (
    <Wrapper>
      <Switch>
        <Route exact path="/planner">
          <AuditPlanner />
        </Route>
        <Route>
          <NotFound />
        </Route>
      </Switch>
    </Wrapper>
  )
}

export default PublicPages
