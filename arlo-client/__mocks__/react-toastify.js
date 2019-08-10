/**
 * Mock for react-toastify
 */

const toast = jest.genMockFromModule('react-toastify')

toast.error = jest.fn()

export default { toast }
