import type {
  ButtonHTMLAttributes,
  ReactNode,
} from "react";

type ButtonVariant = "primary" | "secondary" | "ghost";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  icon?: ReactNode;
};

export function Button({
  variant = "secondary",
  icon,
  className = "",
  children,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`ui-button ui-button--${variant} ${className}`.trim()}
      {...props}
    >
      {icon && (
        <span className="ui-button-icon" aria-hidden="true">
          {icon}
        </span>
      )}

      <span>{children}</span>
    </button>
  );
}