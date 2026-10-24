type EscudoProps = { className?: string }

export const Escudo = ({ className }: EscudoProps) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d="M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6l8-3z" />
    <path d="M12 8.5l1.1 2.2 2.4.3-1.75 1.7.4 2.4L12 14l-2.15 1.1.4-2.4L8.5 11l2.4-.3z" />
  </svg>
)
