import React from 'react';

const FieldSelector = ({ value, onChange, style }) => {
  return (
    <div className="form-group" style={style}>
      <label htmlFor="field-selector" className="form-label">분야 선택</label>
      <select
        id="field-selector"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="form-control"
      >
        <option value="coding">코딩</option>
        <option value="security">보안</option>
        <option value="game">게임 개발</option>
        <option value="art">아트 &amp; 디자인</option>
      </select>
    </div>
  );
};

export default FieldSelector;
