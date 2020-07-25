from collections import Counter
import datetime
import html
import itertools
from os.path import join

import pandas as pd
import streamlit as st


st.title('kaggler-ja FAQ')


@st.cache
def load_excel(year: int, month: int) -> pd.DataFrame:
    DATA_DIR = 'kaggler-ja'
    file_path = join(DATA_DIR, f'{year}-{str(month).zfill(2)}.xlsx')
    df = pd.read_excel(file_path,
                       sheet_name='beginners-help (C6RV8M3DG)',
                       header=None,
                       names=['timestamp', 'user', 'message', 'all'])
    df = df.sort_values('timestamp').dropna().reset_index(drop=True)
    false = False
    df['ts'] = [str(float(eval(d.replace('false', 'False').replace('true', 'True'))['ts']) + 0.01)[:13] for d in df['all']]
    df['url'] = [f'<a href="https://kaggler-ja-slack-archive.appspot.com/?ch=C6RV8M3DG&ts={d}">url</a>' for d in df['ts']]
    df.drop(['all', 'ts'], axis=1, inplace=True)
    return df


def concat_data(start_year: int, start_month: int, end_year: int, end_month: int):
    data = []
    for y in range(start_year, end_year + 1):
        s_m = 1
        e_m = 12
        if y == start_year:
            s_m = start_month
        if y == end_year:
            e_m = end_month
        for m in range(s_m, e_m + 1):
            data.append(load_excel(y, m))
    data = pd.concat(data).reset_index(drop=True)
    data['message'] = data['message'].map(lambda s: html.escape(s))
    return data


if __name__ == '__main__':

    dt_now = datetime.datetime.now()
    start_year_to_filter = st.sidebar.slider('開始年', 2018, 2020, dt_now.year)
    start_month_to_filter = st.sidebar.slider('開始月', 1, 12, dt_now.month)
    end_year_to_filter = st.sidebar.slider('終了年', 2018, 2020, dt_now.year)
    end_month_to_filter = st.sidebar.slider('終了月', 1, 12, dt_now.month)
    condition = start_year_to_filter * 100 + start_month_to_filter <= end_year_to_filter * 100 + end_month_to_filter

    user_input = st.text_input("Search", '')
    data_load_state = st.text('Loading data...')
    if condition:
        data = concat_data(start_year_to_filter, start_month_to_filter, end_year_to_filter, end_month_to_filter)

        if st.checkbox('人気キーワードを表示'):
            import nagisa
            tagger = nagisa.Tagger()
            tags = [tagger.extract(text, extract_postags=['名詞']).words for text in data['message'].sample(n=100, random_state=7)]
            tags = [w for w in list(itertools.chain(*tags)) if len(w) > 2]
            c = Counter(tags)
            st.write(', '.join([d[0] for d in c.most_common(10)]))

        if user_input != '':
            data = data[data['message'].str.contains(user_input, case=False)].reset_index(drop=True)

        data_load_state.subheader(f"{len(data)}件中、最新{min(len(data), 5)}件を表示")
        st.write(data.tail(5).to_html(escape=False), unsafe_allow_html=True)
    else:
        data_load_state.text("Please set valid data range.")
