import React, { useEffect, useRef } from "react";
import { Streamlit } from "streamlit-component-lib";

export const createStreamingChatComponent = () => {
  const StreamingChat = ({ message, is_complete }) => {
    const containerRef = useRef(null);

    useEffect(() => {
      if (is_complete) {
        Streamlit.setFrameHeight();
      }
    }, [message, is_complete]);

    return (
      <div ref={containerRef}>
        {message}
        {!is_complete && <span className="typing-indicator">...</span>}
      </div>
    );
  };

  return StreamingChat;
};
