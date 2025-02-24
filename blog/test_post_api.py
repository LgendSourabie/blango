from datetime import datetime
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from pytz import UTC
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from blog.models import Post


class PostApiTestCase(TestCase):
  
    def setUp(self):
      self.u1 = get_user_model().objects.get_or_create(email="user1@gmail.com", password="pwd_user_1")[0]
      self.u2 = get_user_model().objects.get_or_create(email="user2@gmail.com", password="pwd_user_2")[0]
      posts = [
        Post.objects.create(
                  author=self.u1,
                  published_at=timezone.now(),
                  title="Post 1 Title",
                  slug="post-1-slug",
                  content="Post 1 Content",
        ),
        Post.objects.create(
                  author=self.u2,
                  published_at=timezone.now(),
                  title="Post 2 Title",
                  slug="post-2-slug",
                  content="Post 2 Content",
        ),
      ]
      # look up the post info by ID
      self.post_lookup = {p.id: p for p in posts}

      # Override test client
      self.client = APIClient()
      token_u1 = Token.objects.create(user=self.u1)
      self.client.credentials(HTTP_AUTHORIZATION="Token " + str(token_u1))



    def test_post_list(self):
      """It should list all posts"""

      resp = self.client.get("/api/v1/posts/")
      data = resp.json()["results"]
      self.assertEqual(len(data), 2)

      for post_dict in data:
          post_obj = self.post_lookup[post_dict["id"]]
          self.assertEqual(post_obj.title, post_dict["title"])
          self.assertEqual(post_obj.slug, post_dict["slug"])
          self.assertEqual(post_obj.content, post_dict["content"])
          self.assertTrue(
              post_dict["author"].endswith(f"/api/v1/users/{post_obj.author.email}")
          )
          self.assertEqual(
              post_obj.published_at,
              datetime.strptime(
                  post_dict["published_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
              ).replace(tzinfo=UTC),
          )

    def test_unauthenticated_post_create(self):
      """It should not create a post for unauthenticated user"""

      # unset credentials so we are an anonymous user
      self.client.credentials()
      post_dict = {
          "title": "Test Post",
          "slug": "test-post-3",
          "content": "Test Content",
          "author": "http://testserver/api/v1/users/user1@gmail.com",
          "published_at": "2021-01-10T09:00:00Z",
      }
      resp = self.client.post("/api/v1/posts/", post_dict)
      self.assertEqual(resp.status_code, 401)
      self.assertEqual(Post.objects.all().count(), 2)

    def test_post_create(self):
      """It should create a new post for authenticated user"""
      post_dict = {
          "title": "Test Post",
          "slug": "test-post-3",
          "content": "Test Content",
          "author": "http://testserver/api/v1/users/user1@gmail.com",
          "published_at": "2021-01-10T09:00:00Z",
      }
      resp = self.client.post("/api/v1/posts/", post_dict)
  
      post_id = resp.json()["id"]
      post = Post.objects.get(pk=post_id)
      self.assertEqual(post.title, post_dict["title"])
      self.assertEqual(post.slug, post_dict["slug"])
      self.assertEqual(post.content, post_dict["content"])
      self.assertEqual(post.author, self.u1)
      self.assertEqual(post.published_at, datetime(2021, 1, 10, 9, 0, 0, tzinfo=UTC))