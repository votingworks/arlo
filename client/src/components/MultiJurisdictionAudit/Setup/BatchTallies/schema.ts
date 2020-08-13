import * as Yup from 'yup'

const batchTalliesSchema = Yup.object().shape({
  csv: Yup.mixed().required('You must upload a file'),
})

export default batchTalliesSchema
