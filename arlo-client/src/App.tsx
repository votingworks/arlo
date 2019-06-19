import React from 'react';
import './App.css';
import styled from 'styled-components';
import AuditSetupPage from './pages/AuditSetupPage';

const Main = styled.div`
  height: 100%;
  max-width: 35rem;
  margin: auto auto !important;
  display: block;
  margin: 1.5rem 0 1rem;
  font-size: 1.25rem;
  overflow: scroll;
`

const App: React.FC = () => {
  return (
   
      <Main>
        <AuditSetupPage></AuditSetupPage>
      </Main>
  );
}

export default App;
