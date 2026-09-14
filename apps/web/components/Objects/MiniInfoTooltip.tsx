import React from 'react';
import { motion } from 'motion/react';

interface MiniInfoTooltipProps {
  icon?: React.ReactNode;
  message: string;
  onClose: () => void;
  iconColor?: string;
  iconSize?: number;
  width?: string;
  /**
   * Placement relative to the anchor it is rendered inside.
   *
   * - `top` (default): floats above the anchor. Use when there is clear space
   *   above it.
   * - `inline-start`: sits beside the anchor, vertically centered. Use when the
   *   anchor lives in a fixed bottom bar — `top` puts the tooltip 5rem above the
   *   bar, i.e. directly on top of the page's last line of text, hiding it while
   *   the reader is still reading.
   *
   * **Yet to Dawn fork**: `inline-start` was added for the course activity bar
   * (the two call sites in activity.tsx). The prop is additive; `top` remains
   * the default so existing callers keep their behaviour.
   */
  placement?: 'top' | 'inline-start';
}

export default function MiniInfoTooltip({
  icon,
  message,
  onClose,
  iconColor = 'text-teal-600',
  iconSize = 20,
  width = 'w-48',
  placement = 'top'
}: MiniInfoTooltipProps) {
  const positionClass =
    placement === 'inline-start'
      ? 'absolute end-full me-3 top-1/2 -translate-y-1/2'
      : 'absolute -top-20 left-1/2 transform -translate-x-1/2';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      className={`${positionClass} bg-white rounded-lg nice-shadow p-3 ${width}`}
    >
      <div className="flex items-center space-x-3">
        {icon && (
          <div className={`${iconColor} flex-shrink-0`} style={{ width: iconSize, height: iconSize }}>
            {icon}
          </div>
        )}
        <p className="text-sm text-gray-700">{message}</p>
      </div>
      {/* 箭头指向锚点：上方模式朝下，侧放模式朝内（逻辑属性，跟随书写方向）。 */}
      {placement === 'inline-start' ? (
        <div className="absolute top-1/2 -translate-y-1/2 -end-2 w-4 h-4 bg-white rotate-45"></div>
      ) : (
        <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 w-4 h-4 bg-white rotate-45"></div>
      )}
      <button
        onClick={onClose}
        className="absolute top-1 end-1 text-gray-400 hover:text-gray-600"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </button>
    </motion.div>
  );
}
