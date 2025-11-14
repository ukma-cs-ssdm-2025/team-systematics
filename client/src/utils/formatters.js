const SECONDS_IN_MINUTE = 60
const SECONDS_IN_HOUR = 3600

const HOUR_LABEL = 'год'
const MINUTE_LABEL = 'хв'
const SECOND_LABEL = 'сек'

function pad(num) {
  return String(num).padStart(2, '0')
}

export function formatDuration(totalSeconds) {
  if (typeof totalSeconds !== 'number' || Number.isNaN(totalSeconds) || totalSeconds < 0) {
    totalSeconds = 0;
  }

  const hours = Math.floor(totalSeconds / SECONDS_IN_HOUR)
  const minutes = Math.floor((totalSeconds % SECONDS_IN_HOUR) / SECONDS_IN_MINUTE)
  const seconds = totalSeconds % SECONDS_IN_MINUTE

  if (hours > 0) {
    return `${pad(hours)} ${HOUR_LABEL} ${pad(minutes)} ${MINUTE_LABEL} ${pad(seconds)} ${SECOND_LABEL}`
  } else {
    return `${pad(minutes)} ${MINUTE_LABEL} ${pad(seconds)} ${SECOND_LABEL}`
  }
}