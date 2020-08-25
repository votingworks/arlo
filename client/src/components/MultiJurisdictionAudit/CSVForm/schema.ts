import * as Yup from 'yup'

const csvSchema = Yup.object().shape({
  csv: Yup.mixed().required('You must upload a file'),
})

export default csvSchema
