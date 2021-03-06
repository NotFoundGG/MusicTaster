# coding=utf-8

"""
Created by jayvee on 17/2/22.
https://github.com/JayveeHe
"""
import pickle

import cPickle
from gensim import matutils
from gensim.models.word2vec_inner import REAL
from numpy.core.multiarray import ndarray, array, dot
from sklearn.cluster import AffinityPropagation

from utils.cloudmusic_api import playlist_detail
from utils.logger_utils import data_process_logger


class Song2VecOperator:
    def __init__(self, song2vec_model_path=None, artist2vec_model_path=None):
        """
        初始化,需要填入两种模型的地址
        Args:
            song2vec_model_path:
            artist2vec_model_path:
        """
        try:
            if song2vec_model_path:
                with open(song2vec_model_path, 'rb') as s2v_file:
                    self.song2vec_model = cPickle.load(s2v_file)
                    print self.song2vec_model.estimate_memory()
            if artist2vec_model_path:
                with open(artist2vec_model_path, 'rb') as a2v_file:
                    self.artist2vec_model = cPickle.load(a2v_file)
                    print self.artist2vec_model.estimate_memory()
            self.song2vec_model.init_sims()
            self.artist2vec_model.init_sims()
        except IOError, ioe:
            print '%s' % ioe

    def calc_song_similar(self, positive_songs=[], negative_songs=[],
                          positive_artists=[], negative_artists=[],
                          song_weight=1.0, artist_weight=1.5,
                          topn=10, restrict_vocab=None):
        """
        计算歌曲和歌手的加减相似度,求出最近似的歌曲top n
        Args:
            topn:
            restrict_vocab:
            artist_weight:
            song_weight:
            positive_songs:
            negative_songs:
            positive_artists:
            negative_artists:

        Returns:

        """
        try:
            positive_songs = [(word, song_weight) for word in positive_songs]
            negative_songs = [(word, -song_weight) for word in negative_songs]
            positive_artists = [(word, artist_weight) for word in positive_artists]
            negative_artists = [(word, -artist_weight) for word in negative_artists]
            all_words, mean = set(), []
            if positive_songs + negative_songs:
                for song, weight in positive_songs + negative_songs:
                    song = song.strip()
                    if isinstance(song, ndarray):
                        mean.append(weight * song)
                    elif song in self.song2vec_model.vocab:
                        mean.append(weight * self.song2vec_model.syn0norm[self.song2vec_model.vocab[song].index])
                        all_words.add(self.song2vec_model.vocab[song].index)
                    else:
                        raise KeyError("song '%s' not in vocabulary" % song)
            # limited = self.song2vec_model.syn0norm if restrict_vocab is None \
            #     else self.song2vec_model.syn0norm[:restrict_vocab]
            if positive_artists + negative_artists:
                for artist, weight in positive_artists + negative_artists:
                    if isinstance(word, ndarray):
                        mean.append(weight * artist)
                    elif word in self.artist2vec_model.vocab:
                        mean.append(weight * self.artist2vec_model.syn0norm[self.artist2vec_model.vocab[artist].index])
                        all_words.add(self.artist2vec_model.vocab[artist].index)
                    else:
                        raise KeyError("artist '%s' not in vocabulary" % artist)
            if not mean:
                raise ValueError("cannot compute similarity with no input")
            mean = matutils.unitvec(array(mean).mean(axis=0)).astype(REAL)
            limited = self.song2vec_model.syn0norm if restrict_vocab is None \
                else self.song2vec_model.syn0norm[:restrict_vocab]
            # limited += self.artist2vec_model.syn0norm if restrict_vocab is None \
            #     else self.artist2vec_model.syn0norm[:restrict_vocab]
            dists = dot(limited, mean)
            if not topn:
                return dists
            best = matutils.argsort(dists, topn=topn + len(all_words), reverse=True)
            # ignore (don't return) words from the input
            result = [(self.song2vec_model.index2word[sim], float(dists[sim])) for sim in best if sim not in all_words]
            return result[:topn]
        except Exception, e:
            print 'error = %s' % e
            raise e

    def calc_artist_similar(self, positive_songs=[], negative_songs=[],
                            positive_artists=[], negative_artists=[],
                            song_weight=1.0, artist_weight=1.5,
                            topn=10, restrict_vocab=None):
        """
        计算歌曲和歌手的加减相似度,求出最近似的歌手top n
        Args:
            topn:
            restrict_vocab:
            artist_weight:
            song_weight:
            positive_songs:
            negative_songs:
            positive_artists:
            negative_artists:

        Returns:

        """
        try:
            positive_songs = [(word, song_weight) for word in positive_songs]
            negative_songs = [(word, -song_weight) for word in negative_songs]
            positive_artists = [(word, artist_weight) for word in positive_artists]
            negative_artists = [(word, -artist_weight) for word in negative_artists]
            all_words, mean = set(), []
            if positive_songs + negative_songs:
                for song, weight in positive_songs + negative_songs:
                    if isinstance(song, ndarray):
                        mean.append(weight * song)
                    elif song in self.song2vec_model.vocab:
                        mean.append(weight * self.song2vec_model.syn0norm[self.song2vec_model.vocab[song].index])
                        all_words.add(self.song2vec_model.vocab[song].index)
                    else:
                        raise KeyError("song '%s' not in vocabulary" % song)
            # limited = self.song2vec_model.syn0norm if restrict_vocab is None \
            #     else self.song2vec_model.syn0norm[:restrict_vocab]
            if positive_artists + negative_artists:
                for artist, weight in positive_artists + negative_artists:
                    if isinstance(word, ndarray):
                        mean.append(weight * artist)
                    elif word in self.artist2vec_model.vocab:
                        mean.append(weight * self.artist2vec_model.syn0norm[self.artist2vec_model.vocab[artist].index])
                        all_words.add(self.artist2vec_model.vocab[artist].index)
                    else:
                        raise KeyError("artist '%s' not in vocabulary" % artist)
            if not mean:
                raise ValueError("cannot compute similarity with no input")
            mean = matutils.unitvec(array(mean).mean(axis=0)).astype(REAL)
            limited = self.artist2vec_model.syn0norm if restrict_vocab is None \
                else self.artist2vec_model.syn0norm[:restrict_vocab]
            # limited += self.artist2vec_model.syn0norm if restrict_vocab is None \
            #     else self.artist2vec_model.syn0norm[:restrict_vocab]
            dists = dot(limited, mean)
            if not topn:
                return dists
            best = matutils.argsort(dists, topn=topn + len(all_words), reverse=True)
            # ignore (don't return) words from the input
            result = [(self.artist2vec_model.index2word[sim], float(dists[sim])) for sim in best if
                      sim not in all_words]
            return result[:topn]
        except Exception, e:
            print 'error = %s' % e
            raise e

    def cluster_song_in_playlist(self, playlist_id, cluster_n=5, is_detailed=False):
        """
        获取单个歌单内的歌曲聚类信息
        Args:
            playlist_id: 歌单id
            cluster_n:聚类数
            is_detailed: 返回的结果是否包含详情

        Returns:
            聚类后的列表
        """
        playlist_obj = playlist_detail(playlist_id)
        song_list = []
        vec_list = []
        song_info_dict = {}
        ap_cluster = AffinityPropagation()
        data_process_logger.info('clustering playlist: %s' % playlist_obj['name'])
        for item in playlist_obj['tracks']:
            song = item['name'].lower()
            song_info_dict[song] = {
                'name': song,
                'artist': item['artists'][0]['name'],
                'id': item['id'],
                'album_img_url': item['album']['picUrl'],
                'site_url': 'http://music.163.com/#/song?id=%s' % item['id']
            }
            # print song
            if song not in song_list:
                song_list.append(song)
                # print self.song2vec_model.vocab.get(song)
                # print self.song2vec_model.syn0norm == None
                if self.song2vec_model.vocab.get(song) and len(self.song2vec_model.syn0norm):
                    song_vec = self.song2vec_model.syn0norm[self.song2vec_model.vocab[song].index]
                else:
                    data_process_logger.warn(
                        'The song %s of playlist-%s is not in dataset' % (song, playlist_obj['name']))
                    song_vec = [0 for i in range(self.song2vec_model.vector_size)]
                vec_list.append(song_vec)
        # song_list = list(song_list)
        if len(vec_list) > 1:
            cluster_result = ap_cluster.fit(vec_list, song_list)
            cluster_array = [[] for i in range(len(cluster_result.cluster_centers_indices_))]
            for i in range(len(cluster_result.labels_)):
                label = cluster_result.labels_[i]
                index = i
                cluster_array[label].append(song_list[i])
            return cluster_array, playlist_obj['name'], song_info_dict
        else:
            return [song_list], playlist_obj['name'], song_info_dict

    def cluster_artist_in_playlist(self, playlist_id, cluster_n=5, is_detailed=False):
        """
        获取单个歌单内的歌手聚类信息
        Args:
            playlist_id: 歌单id
            cluster_n:聚类数
            is_detailed: 是否包含详情信息

        Returns:
            聚类后的列表
        """
        playlist_obj = playlist_detail(playlist_id)
        artist_list = []
        vec_list = []
        ap_cluster = AffinityPropagation()
        data_process_logger.info('clustering playlist: %s' % playlist_obj['name'])
        for item in playlist_obj['tracks']:
            artist = item['artists'][0]['name'].lower()
            # print artist
            if artist not in artist_list:
                artist_list.append(artist)
                # print self.song2vec_model.vocab.get(artist)
                # print self.song2vec_model.syn0norm == None
                if self.artist2vec_model.vocab.get(artist) and len(self.artist2vec_model.syn0norm):
                    artist_vec = self.artist2vec_model.syn0norm[self.artist2vec_model.vocab[artist].index]
                else:
                    data_process_logger.warn(
                        'The artist %s of playlist-%s is not in dataset' % (artist, playlist_obj['name']))
                    artist_vec = [0 for i in range(self.artist2vec_model.vector_size)]
                vec_list.append(artist_vec)
        # artist_list = list(artist_list)
        # vec_list = list(vec_list)
        if len(vec_list) > 1:
            cluster_result = ap_cluster.fit(vec_list, artist_list)
            cluster_array = [[] for i in range(len(cluster_result.cluster_centers_indices_))]
            for i in range(len(cluster_result.labels_)):
                label = cluster_result.labels_[i]
                index = i
                cluster_array[label].append(artist_list[i])
            return cluster_array, playlist_obj['name'], {}
        else:
            return [artist_list], playlist_obj['name'], {}


if __name__ == '__main__':
    s2vo = Song2VecOperator(song2vec_model_path='../datas/[full]50d_20iter_10win_5min_song2vec.model',
                            artist2vec_model_path='../datas/[full]50d_20iter_10win_5min_artist2vec.model')
    # res = s2vo.calc_song_artist_similar(positive_songs=[u'time machine', u'yellow', u'viva la vida'],
    #                                     negative_songs=[],
    #                                     positive_artists=[],
    #                                     negative_artists=[],
    #                                     artist_weight=1.0, topn=20)
    # for i in res:
    #     print i[0], i[1]
    s2vo.cluster_song_in_playlist('3659853')
    # s2vo.cluster_artist_in_playlist('3659853')
