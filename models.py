#from my_preprocess_new_with_paseqs import *
#from hebrew_text_processing import *
from sqlalchemy import create_engine, Column, ForeignKey
from sqlalchemy import Integer, String
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Mapped, mapped_column, DeclarativeBase
from typing import List, Optional, Dict

db_url = "sqlite:///database.db"

engine = create_engine(db_url) #echo=True

Session = sessionmaker(bind=engine)
session = Session()

class Base(DeclarativeBase):
    pass

class Parsing(Base):
    __tablename__ = 'parsings'
    id: Mapped[int] = mapped_column(primary_key=True)
    book: Mapped[str] = mapped_column(String(4))
    chapter: Mapped[int] = mapped_column(String(3))
    verse: Mapped[int] = mapped_column(String(4))
    half_verse: Mapped[str] = mapped_column(String(1))
    parsing_num: Mapped[int] = mapped_column(default=1)
    gvpath: Mapped[str]
    nodes: Mapped[Optional[List["CNode"]]] = relationship(back_populates="parsing", uselist=True)

    def __repr__(self):
        return f"<{self.book} {self.chapter}:{self.verse}{self.half_verse} parsing {self.parsing_num}>"
    
    def root(self):
        return self.nodes[0]

class CNode(Base):
    __tablename__ = "nodes"
    id: Mapped[int] =  mapped_column(primary_key=True)
    mother_id: Mapped[Optional[int]] = mapped_column(ForeignKey("nodes.id"))  
    bloodline: Mapped[Optional[str]]
    parsing_id: Mapped[int] = mapped_column(ForeignKey("parsings.id"))
    parsing: Mapped["Parsing"] = relationship(back_populates="nodes")
    children: Mapped[Optional[List["CNode"]]] = relationship(back_populates="mother")
    mother = relationship("CNode", back_populates="children", remote_side=[id])
    name: Mapped[Optional[str]]
    accent_rank: Mapped[Optional[int]]
    cont_words: Mapped[Optional[List["Word"]]] = relationship(back_populates="mother_node", uselist=True)

    def add_bl(self):
        if self.mother:
            self.bloodline = f"{self.mother.bloodline}>{self.id}"
        else:
            self.bloodline = f"{self.id}"

    def root(self):
        assert self.bloodline
        root_id = int(self.bloodline.split('>')[0])
        return session.query(CNode).filter_by(id=root_id).one_or_none()

    def __contains__(self, item):
        return item in self.children
    
    def __iter__(self):
        return iter(self.children)
    
    def __next__(self):
        return next(self.children)     

    def __le__(self, node):
        return self in node or node == self

    def __lt__(self, node):
        return self in node
    
    def __ge__(self, node):
        return node in self or node == self

    def __gt__(self, node):
        return node in self
    
    def min_cc(self, node):
        if self >= node:
            return self
        elif node > self:
            return node
        else:
            if node.mother and self.mother:
                return min(CNode.min_cc(self.mother, node),
                        CNode.min_cc(self, node.mother))
            elif node.mother:
                return self.min_cc(node.mother)
            elif self.mother:
                return self.mother.min_cc(node)

class Word(Base):
    __tablename__ = "words"
    id: Mapped[int] = mapped_column(primary_key=True)
    mother_node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"))
    mother_node: Mapped["CNode"] = relationship(back_populates="cont_words")
    pos: Mapped[str] = mapped_column(nullable=False)
    agr: Mapped[Optional[str]]
    p_suffix: Mapped[Optional[str]]
    verb_stem: Mapped[Optional[str]]
    tense_etc: Mapped[Optional[str]]
    state: Mapped[Optional[str]]
    lemma: Mapped[str] = mapped_column(nullable=False)
    aramaic: Mapped[Optional[bool]]

    def __repr__(self):
        return f"<Word {self.id}, lemma: {self.lemma}, pos: {self.pos}>"


Base.metadata.create_all(engine)


# will finish


