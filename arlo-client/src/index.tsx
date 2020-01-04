import 'react-app-polyfill/ie11'
import React from 'react'
import ReactDOM from 'react-dom'
import './index.css'
import App from './App'
import * as serviceWorker from './serviceWorker'
import { Auth0Provider } from './react-auth0-spa'
import config from './auth_config.json'
import history from './utils/history'

interface Auth0RedirectState {
  targetUrl?: string
}

const Auth0 = Auth0Provider as ({ children, onRedirectCallback, ...initOptions }: {
  [x: string]: any;
  children: any;
  onRedirectCallback?: ((appState: Auth0RedirectState) => void) | undefined;
}) => JSX.Element

// A function that routes the user to the right place
// after login
const onRedirectCallback = (appState: Auth0RedirectState) => {
    history.push(
      appState && appState.targetUrl
        ? appState.targetUrl
        : window.location.pathname
    );
  };

ReactDOM.render(
    <Auth0
      domain={config.domain}
      client_id={config.clientId}
      redirect_uri={window.location.origin}
      onRedirectCallback={onRedirectCallback}
    >
      <App />
    </Auth0>,
    document.getElementById("root")
  );

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister()

