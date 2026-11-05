// 'YYYY-MM-DD' -> local midnight. new Date('YYYY-MM-DD') is UTC midnight and shows the day before west of UTC.
export const parseLocalDate = (value) => {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(value)
  return m ? new Date(+m[1], +m[2] - 1, +m[3]) : new Date(value)
}
