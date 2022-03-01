/**
 * Some counties in our map topology data have names that are difficult to match
 * to jurisdictions. For example, in Virginia, Richmond County and Richmond City
 * are different jurisdictions, and the topology has separate geometries for each,
 * but they are both named "Richmond". This mapping allows us to rename
 * individual county geometries so we can accurately match them to
 * jurisdictions provided by the audit admin.
 */
interface MapCountyCorrections {
  [state: string]: {
    [countyId: string]: string
  }
}
const mapCountyCorrections: MapCountyCorrections = {
  Virginia: {
    '51510': 'Alexandria City',
    '51520': 'Bristol City',
    '51530': 'Buena Vista City',
    '51540': 'Charlottesville City',
    '51550': 'Chesapeake City',
    '51570': 'Colonial Heights City',
    '51580': 'Covington City',
    '51590': 'Danville City',
    '51595': 'Emporia City',
    '51600': 'Fairfax City',
    '51620': 'Franklin City',
    '51630': 'Fredericksburg City',
    '51640': 'Galax City',
    '51650': 'Hampton City',
    '51660': 'Harrisonburg City',
    '51670': 'Hopewell City',
    '51097': 'King & Queen County',
    '51678': 'Lexington City',
    '51680': 'Lynchburg City',
    '51683': 'Manassas City',
    '51685': 'Manassas Park City',
    '51690': 'Martinsville City',
    '51700': 'Newport News City',
    '51710': 'Norfolk City',
    '51720': 'Norton City',
    '51730': 'Petersburg City',
    '51735': 'Poquoson City',
    '51740': 'Portsmouth City',
    '51750': 'Radford City',
    '51159': 'Richmond County',
    '51760': 'Richmond City',
    '51770': 'Roanoke City',
    '51775': 'Salem City',
    '51790': 'Staunton City',
    '51800': 'Suffolk City',
    '51820': 'Waynesboro City',
    '51840': 'Winchester City',
    '51830': 'Williamsburg City',
  },
}
export default mapCountyCorrections
