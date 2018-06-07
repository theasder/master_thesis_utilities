#encoding "utf-8"

S -> NamePhrase | PhraseName | ShortIntro | VeryShortIntro | OneMoreIntro;
NamePhrase -> ("мень") "звать" FIO;
PhraseName -> "я" ("-") FIO;
ShortIntro -> FIO<fw> "," IntroWord;
IntroWord -> Noun | Verb | Adj | EOSent;
VeryShortIntro -> Word EOSent FIO;
OneMoreIntro -> "представляться" ";" FIO;
FIO -> proper_name_1 | proper_name_2 | proper_name_3;
proper_name_1 -> Surname interp (Fact.Surname::not_norm) Name interp (Fact.Name::not_norm);
proper_name_2 -> Name interp (Fact.Name::not_norm) Surname interp (Fact.Surname::not_norm);
proper_name_3 -> Name interp (Fact.Name::not_norm);
Surname -> AnyWord<h-reg1, wff=/.*(ов|ын|ин|ев|ко|ян)а*/> | AnyWord<h-reg1, wfl=/.*(ов|ын|ин|ев|ко|ян)а*/> | AnyWord<h-reg1, wfm=/.*(ов|ын|ин|ев|ко|ян)а*/> | Word<gram='фам', h-reg1> | Word<h-reg1, wfl=/[А-Я][ёа-я]+/>;
Name -> Word<gram='имя', h-reg1>;

