from typing import Any, Optional, Union, List, Dict
from unittest.mock import Base
from pydantic import BaseModel, Field

import datetime

class ERISDataRow(BaseModel):
    timestamp: datetime.datetime = Field(alias='time')
    tag: str = Field(alias='source')
    value: Union[float, int] = Field(alias='value')

class ERISData(BaseModel):
    tagUID: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    engUnits: Optional[str] = None
    sampleInterval: Optional[str] = None
    samplingMode: Optional[str] = None
    data: Optional[List[ERISDataRow]] = None
    provider: Optional[str] = None
    eris_tag: Optional['ERISTag'] = None

class RawERISDataRow(BaseModel):
    annotationText: Optional[List] = None
    time: Optional[datetime.datetime] = None
    valueQualifier: Optional[str] = None
    value: Optional[Union[float]] = None
    initialValueQualifier: Optional[str] = None
    initialValue: Optional[Any] = None
    quality: Optional[Union[float]] = None
    source: Optional[str] = None
    comments: Optional[str] = None
    flags: Optional[str] = None
    annotations: Optional[Union[List, str]] = None
    valid: Optional[bool] = None
    limit: Optional[str] = None
    colour: Optional[str] = None
    operator: Optional[str] = None
    use: Optional[bool] = None
    status: Optional[str] = None
    reviewRequired: Optional[bool] = None
    reviewed: Optional[bool] = None
    final: Optional[bool] = None

class RawERISTag(BaseModel):
    tagUID: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    engUnits: Optional[str] = None
    sampleInterval: Optional[str] = None
    samplingMode: Optional[str] = None
    descriptor:  Optional[List[Any]] = None
    annotation: Optional[List[Any]] = None
    data: List[RawERISDataRow]
    start: Optional[datetime.datetime] = None
    end: Optional[datetime.datetime] = None
    requestor: Optional[str] = None
    provider: Optional[str] = None
    cacheable: Optional[bool] = None
    inputType: Optional[str] = None

class RawERISResponse(BaseModel):
    tags: List[RawERISTag] = Field(alias='tag')