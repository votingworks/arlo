import * as Yup from 'yup'

const ballotManifestSchema = Yup.object().shape({
  csv: Yup.mixed().required('You must upload a file'),
})

export default ballotManifestSchema
