// test-setup.js
import { configure } from 'enzyme'
import Adapter from 'enzyme-adapter-react-16'
import '@testing-library/jest-dom/extend-expect'
import '@testing-library/react/cleanup-after-each'

configure({ adapter: new Adapter() })

jest.mock('./components/utilities')
