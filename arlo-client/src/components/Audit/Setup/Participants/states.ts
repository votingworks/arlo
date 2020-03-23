import locale from '../../../../locales/current'

export default Object.keys(locale.usState).map(value => ({
  value,
  label: locale.usState[value as keyof typeof locale.usState],
}))
