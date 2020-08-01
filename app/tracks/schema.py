import graphene
from graphene_django import DjangoObjectType
from graphql import GraphQLError
from django.db.models import Q

from .models import Track, Like
from users.schema import UserType

class TrackType(DjangoObjectType):
    class Meta:
        model = Track

class LikeType(DjangoObjectType):

  class Meta:
    model = Like


class Query(graphene.ObjectType):
    tracks = graphene.List(TrackType, search=graphene.String())
    likes = graphene.List(LikeType)

    def resolve_tracks(self, info, search = None):
      if search:
        filter =(
          Q(title__icontains = search) | 
          Q(description__icontains = search) | 
          Q(url__icontains = search) | 
          Q(posted_by__username__icontains = search))
          
        return Track.objects.filter(filter)
      return Track.objects.all()

    def resolve_likes(self, info):
      return Like.objects.all()

class CreateTrack(graphene.Mutation):
    track = graphene.Field(TrackType)

    class Arguments:
        title = graphene.String()
        description = graphene.String()
        url = graphene.String()

    def mutate(self, info, title, description, url):
        user = info.context.user or None

        if user.is_anonymous:
          raise GraphQLError('Login to add a new Track')
        track = Track(title=title, description=description,
                      url=url, posted_by = user)
        track.save()
        return CreateTrack(track=track)

class UpdateTrack(graphene.Mutation):
  track = graphene.Field(TrackType)

  class Arguments: 
    track_id = graphene.Int(required = True)
    title = graphene.String()
    description = graphene.String()
    url = graphene.String()

  def mutate(self, info, track_id, title, url, description):
    user = info.context.user
    track = Track.objects.get(id = track_id)

    if track.posted_by != user:
      raise GraphQLError('No esta permitido editar tracks de otros actores')

    track.title = title
    track.url = url
    track.description = description
    track.save()

    return UpdateTrack(track = track)

class DeleteTrack(graphene.Mutation):
  track_id = graphene.Int()

  class Arguments:
    track_id = graphene.Int(required= True)
  
  def mutate(self, info, track_id):
    user = info.context.user
    track = Track.objects.get(id = track_id)

    if track.posted_by != user:
      raise GraphQLError("No puedes borrar tracks de otros autores")

    track.delete()
    return DeleteTrack(track_id = track_id)

class CreateLike(graphene.Mutation):
  user = graphene.Field(UserType)
  track = graphene.Field(TrackType)

  class Arguments: 
    track_id = graphene.Int(required = True)

  def mutate(self, info, track_id):
    user = info.context.user

    if user.is_anonymous:
      raise GraphQLError('Debes iniciar sesion para dar like a un track')

    track = Track.objects.get(id = track_id)
    if not track:
      raise GraphQLError('No se pudo encontrar el track')
    Like.objects.create(
      user = user,
      track = track
    )

    return CreateLike(user = user, track = track)


class Mutation(graphene.ObjectType):
    create_track = CreateTrack.Field()
    update_track = UpdateTrack.Field()
    delete_track = DeleteTrack.Field()
    create_like = CreateLike.Field()


