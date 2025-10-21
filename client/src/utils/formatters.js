const SECONDS_IN_MINUTE = 60;
const MINUTE_LABEL = 'хв';
const SECOND_LABEL = 'сек';

export function formatDuration(totalSeconds) {
  if (totalSeconds >= 3600) {
    const hours = Math.floor(totalSeconds / 3600)
    const minutes = Math.floor((totalSeconds % 3600) / 60)
    const seconds = totalSeconds % 60

    const paddedHours = String(hours).padStart(2, '0')
    const paddedMinutes = String(minutes).padStart(2, '0')
    const paddedSeconds = String(seconds).padStart(2, '0')

    return `${paddedHours} год ${paddedMinutes} ${MINUTE_LABEL} ${paddedSeconds} ${SECOND_LABEL}`;
  }

  const minutes = Math.floor(totalSeconds / SECONDS_IN_MINUTE)
  const seconds = totalSeconds % SECONDS_IN_MINUTE

  const paddedMinutes = String(minutes).padStart(2, '0')
  const paddedSeconds = String(seconds).padStart(2, '0')

  return `${paddedMinutes} ${MINUTE_LABEL} ${paddedSeconds} ${SECOND_LABEL}`
}